import base64
import io
import secrets
import time

import pyotp
import qrcode
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user
from flask_mail import Message

from backend.extensions import limiter, mail
from database.models import db
from database.models.user import User
from backend.utils.security import hash_token
from backend.routes.pages import serve_frontend_page

security_bp = Blueprint("security", __name__, url_prefix="/security")


@security_bp.route("/verify/<token>")
@limiter.limit("5 per minute")
def verify_email(token):
    user = db.session.query(User).filter_by(verification_token=hash_token(token)).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        if request.is_json:
            return jsonify({"success": True, "message": "Your email has been successfully verified! You can now log in."})
        flash("Your email has been successfully verified! You can now log in.", "success")
    else:
        if request.is_json:
            return jsonify({"success": False, "message": "Invalid or expired verification link."}), 400
        flash("Invalid or expired verification link.", "danger")
    return redirect(url_for("auth.customer_login"))


@security_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == "GET":
        return serve_frontend_page("customer.html")

    # POST — process forgot-password
    if request.is_json:
        email = (request.json.get("email", "") or "").strip().lower()
    else:
        email = request.form.get("email", "").strip().lower()
    
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        raw_token = secrets.token_urlsafe(32)
        token = f"{raw_token}.{int(time.time())}"
        user.reset_token = hash_token(token)
        db.session.commit()
        try:
            msg = Message(
                "Password Reset Request | e Grossary Store",
                recipients=[user.email],
            )
            reset_url = url_for("security.reset_password", token=token, _external=True)
            msg.body = f"Click here to reset your password: {reset_url}\nThis link expires in 15 minutes. If you did not request this, please ignore it."
            mail.send(msg)
        except Exception:
            current_app.logger.exception("Failed to send password reset email")

    message = "If an account matches that email, a password reset link has been sent."
    if request.is_json:
        return jsonify({"success": True, "message": message})
    flash(message, "info")
    return redirect(url_for("auth.customer_login"))


@security_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def reset_password(token):
    # Enforce 15-minute token expiration
    if "." in token:
        try:
            _, ts_str = token.rsplit(".", 1)
            token_time = int(ts_str)
            if time.time() - token_time > 900:  # 15 minutes
                msg = "This password reset link has expired. Please request a new one."
                if request.is_json:
                    return jsonify({"success": False, "message": msg}), 400
                flash(msg, "danger")
                return redirect(url_for("auth.customer_login"))
        except (ValueError, TypeError):
            pass

    user = db.session.query(User).filter_by(reset_token=hash_token(token)).first()
    if not user:
        if request.is_json:
            return jsonify({"success": False, "message": "Invalid or expired reset token."}), 400
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for("auth.customer_login"))

    if request.method == "GET":
        return serve_frontend_page("customer.html")

    # POST — process password reset
    if request.is_json:
        password = request.json.get("password", "")
        confirm_password = request.json.get("confirm_password", "")
    else:
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

    min_length = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
    if not password or len(password) < min_length:
        msg = f"Password must be at least {min_length} characters."
        if request.is_json:
            return jsonify({"success": False, "message": msg}), 400
        flash(msg, "danger")
    elif password in ("password", "password123", "12345678", "admin123", "qwertyuiop"):
        msg = "Password is too common or easily guessed."
        if request.is_json:
            return jsonify({"success": False, "message": msg}), 400
        flash(msg, "danger")
    elif password != confirm_password:
        msg = "Passwords do not match."
        if request.is_json:
            return jsonify({"success": False, "message": msg}), 400
        flash(msg, "danger")
    else:
        from werkzeug.security import generate_password_hash

        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        db.session.commit()
        msg = "Your password has been reset successfully. You can now log in."
        if request.is_json:
            return jsonify({"success": True, "message": msg, "redirect": url_for("auth.customer_login")})
        flash(msg, "success")
        return redirect(url_for("auth.customer_login"))

    return serve_frontend_page("customer.html")


@security_bp.route("/setup-2fa", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def setup_2fa():
    if not current_user.is_authenticated or current_user.role != "admin":
        if request.is_json:
            return jsonify({"success": False, "message": "Unauthorized."}), 403
        return redirect(url_for("auth.login"))

    if current_user.two_factor_enabled:
        if request.is_json:
            return jsonify({"success": False, "message": "2FA is already enabled."})
        flash("2FA is already enabled.", "info")
        return redirect(url_for("admin.dashboard"))

    if request.method == "GET":
        if not current_user.two_factor_secret:
            current_user.two_factor_secret = pyotp.random_base32()
            db.session.commit()

        totp = pyotp.TOTP(current_user.two_factor_secret)
        uri = totp.provisioning_uri(
            name=current_user.email, issuer_name="e Grossary Store"
        )

        qr = qrcode.make(uri)
        img_io = io.BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)
        qr_b64 = base64.b64encode(img_io.getvalue()).decode("utf-8")

        return jsonify({
            "qr_code": f"data:image/png;base64,{qr_b64}",
            "secret": current_user.two_factor_secret,
            "provisioning_uri": uri,
        })

    if request.method == "POST":
        if request.is_json:
            token = request.json.get("token", "")
        else:
            token = request.form.get("token")
        totp = pyotp.TOTP(current_user.two_factor_secret)

        if totp.verify(token, valid_window=1):
            current_user.two_factor_enabled = True
            db.session.commit()
            if request.is_json:
                return jsonify({"success": True, "message": "2FA successfully enabled!"})
            flash("2FA successfully enabled!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            if request.is_json:
                return jsonify({"success": False, "message": "Invalid code. Please try again."}), 400
            flash("Invalid code. Please try again.", "danger")
            return redirect(url_for("security.setup_2fa"))


@security_bp.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def verify_2fa():
    if "2fa_user_id" not in session or "2fa_expires_at" not in session:
        if request.is_json:
            return jsonify({"success": False, "message": "No 2FA session found."}), 400
        return redirect(url_for("auth.login"))
        
    if time.time() > session["2fa_expires_at"]:
        session.pop("2fa_user_id", None)
        session.pop("2fa_expires_at", None)
        if request.is_json:
            return jsonify({"success": False, "message": "2FA session expired. Please log in again."}), 400
        flash("2FA session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["2fa_user_id"])
    if not user or not user.two_factor_secret:
        return jsonify({"success": False, "message": "Invalid 2FA account state."}), 400

    if request.method == "GET":
        return serve_frontend_page("admin.html")

    # POST — verify 2FA code
    if request.is_json:
        token = str(request.json.get("token", "")).strip()
    else:
        token = str(request.form.get("token", "")).strip()
    totp = pyotp.TOTP(user.two_factor_secret)

    if totp.verify(token, valid_window=1):
        session.pop("2fa_user_id", None)
        session.pop("2fa_expires_at", None)
        old_cart = session.get("cart")
        session.clear()
        if old_cart:
            session["cart"] = old_cart
        login_user(user)
        if request.is_json:
            return jsonify({"success": True, "message": "Login successful!", "redirect": url_for("admin.dashboard")})
        flash("Login successful!", "success")
        return redirect(url_for("admin.dashboard"))
    else:
        if request.is_json:
            return jsonify({"success": False, "message": "Invalid 2FA code."}), 400
        flash("Invalid 2FA code.", "danger")

    return serve_frontend_page("admin.html")

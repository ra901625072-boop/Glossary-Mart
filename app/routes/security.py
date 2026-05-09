import base64
import io
import secrets

import pyotp
import qrcode
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user
from flask_mail import Message

from app.extensions import limiter
from app.models import User, db
from app.utils import hash_token

security_bp = Blueprint("security", __name__, url_prefix="/security")


@security_bp.route("/verify/<token>")
@limiter.limit("5 per minute")
def verify_email(token):
    user = db.session.query(User).filter_by(verification_token=hash_token(token)).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash("Your email has been successfully verified! You can now log in.", "success")
    else:
        flash("Invalid or expired verification link.", "danger")
    return redirect(url_for("auth.customer_login"))


@security_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = hash_token(token)
            db.session.commit()
            try:
                from app import mail

                msg = Message(
                    "Password Reset Request | Jay Goga Kirana Store",
                    recipients=[user.email],
                )
                reset_url = url_for("security.reset_password", token=token, _external=True)
                msg.body = f"Click here to reset your password: {reset_url}\nIf you did not request this, please ignore it."
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Error sending password reset email: {str(e)}")

        flash(
            "If an account matches that email, a password reset link has been sent.", "info"
        )
        return redirect(url_for("auth.customer_login"))
    return render_template("customer/forgot_password.html")


@security_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def reset_password(token):
    user = db.session.query(User).filter_by(reset_token=hash_token(token)).first()
    if not user:
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for("auth.customer_login"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        else:
            from werkzeug.security import generate_password_hash

            user.password_hash = generate_password_hash(password)
            user.reset_token = None
            db.session.commit()
            flash("Your password has been reset successfully. You can now log in.", "success")
            return redirect(url_for("auth.customer_login"))

    return render_template("customer/reset_password.html", token=token)


@security_bp.route("/setup-2fa", methods=["GET", "POST"])
def setup_2fa():
    if not current_user.is_authenticated or current_user.role != "admin":
        return redirect(url_for("auth.login"))

    if current_user.two_factor_enabled:
        flash("2FA is already enabled.", "info")
        return redirect(url_for("admin.dashboard"))

    if request.method == "GET":
        if not current_user.two_factor_secret:
            current_user.two_factor_secret = pyotp.random_base32()
            db.session.commit()

        totp = pyotp.TOTP(current_user.two_factor_secret)
        uri = totp.provisioning_uri(
            name=current_user.email, issuer_name="Jay Goga Kirana Store"
        )

        qr = qrcode.make(uri)
        img_io = io.BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)
        qr_b64 = base64.b64encode(img_io.getvalue()).decode("utf-8")

        return render_template(
            "admin/setup_2fa.html",
            qr_b64=qr_b64,
            secret=current_user.two_factor_secret,
        )

    if request.method == "POST":
        token = request.form.get("token")
        totp = pyotp.TOTP(current_user.two_factor_secret)

        if totp.verify(token):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash("2FA successfully enabled!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid code. Please try again.", "danger")
            return redirect(url_for("security.setup_2fa"))


@security_bp.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    if "2fa_user_id" not in session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["2fa_user_id"])

    if request.method == "POST":
        token = request.form.get("token")
        totp = pyotp.TOTP(user.two_factor_secret)

        if totp.verify(token):
            login_user(user)
            session.pop("2fa_user_id", None)
            flash("Login successful!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid 2FA code.", "danger")

    return render_template("admin/verify_2fa.html")

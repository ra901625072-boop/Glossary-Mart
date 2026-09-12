import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Union

from flask import current_app, render_template, url_for

from backend.extensions import mail

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized email delivery service supporting:
    1. Direct Resend REST API (HTTPS port 443 — works on Render, Vercel, serverless).
    2. Fallback to Flask-Mail SMTP (for local dev or custom SMTP servers).
    3. Sandbox domain awareness (onboarding@resend.dev restrictions).
    """

    RESEND_API_URL = "https://api.resend.com/emails"

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Returns RESEND_API_KEY from Flask app config or environment."""
        if current_app:
            key = current_app.config.get("RESEND_API_KEY")
            if key:
                return key.strip()
        key = os.getenv("RESEND_API_KEY")
        return key.strip() if key else None

    @classmethod
    def get_default_sender(cls) -> str:
        """Returns formatted default sender address."""
        raw_sender = None
        if current_app:
            raw_sender = current_app.config.get("MAIL_DEFAULT_SENDER")
        if not raw_sender:
            raw_sender = os.getenv("MAIL_DEFAULT_SENDER", "onboarding@resend.dev")

        raw_sender = raw_sender.strip()
        if "<" not in raw_sender and "@" in raw_sender:
            return f"eGrossary <{raw_sender}>"
        return raw_sender

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if either Resend API key or SMTP is configured."""
        if cls.get_api_key():
            return True
        if current_app:
            return bool(current_app.config.get("MAIL_USERNAME"))
        return bool(os.getenv("MAIL_USERNAME"))

    @classmethod
    def send_via_resend_api(
        cls,
        api_key: str,
        to: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends transactional email via Resend HTTPS REST API.
        Does not require outbound SMTP ports (never blocked by Render/Vercel).
        """
        recipients = [to] if isinstance(to, str) else list(to)
        from_address = sender or cls.get_default_sender()

        payload: Dict[str, Any] = {
            "from": from_address,
            "to": recipients,
            "subject": subject,
        }

        if html_content:
            payload["html"] = html_content
        if text_content:
            payload["text"] = text_content
        elif not html_content:
            payload["text"] = subject

        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            cls.RESEND_API_URL,
            data=body_bytes,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "resend-python/2.0.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                email_id = resp_data.get("id")
                logger.info(
                    "Resend email sent successfully (ID: %s) to %s",
                    email_id,
                    recipients,
                )
                return {
                    "success": True,
                    "provider": "resend_api",
                    "id": email_id,
                    "message": "Email sent successfully via Resend API",
                }
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            logger.warning(
                "Resend API HTTP %s: %s | Recipients: %s",
                err.code,
                err_body,
                recipients,
            )

            # Check if this is the standard Resend sandbox restriction
            is_sandbox_restriction = (
                "only send testing emails to your own email address" in err_body
                or err.code == 403
            )
            return {
                "success": False,
                "provider": "resend_api",
                "status_code": err.code,
                "error": err_body,
                "is_sandbox_restriction": is_sandbox_restriction,
                "message": (
                    "Resend test sandbox restriction: unverified recipient address."
                    if is_sandbox_restriction
                    else f"Resend API returned status {err.code}."
                ),
            }
        except Exception as ex:
            logger.exception("Unexpected error sending email via Resend API: %s", ex)
            return {
                "success": False,
                "provider": "resend_api",
                "error": str(ex),
                "message": f"Failed to send email via Resend API: {ex}",
            }

    @classmethod
    def send_via_smtp(
        cls,
        to: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fallback to Flask-Mail SMTP."""
        from flask_mail import Message

        recipients = [to] if isinstance(to, str) else list(to)
        from_address = sender or cls.get_default_sender()

        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                sender=from_address,
            )
            if html_content:
                msg.html = html_content
            if text_content:
                msg.body = text_content
            elif not html_content:
                msg.body = subject

            mail.send(msg)
            logger.info("Email sent successfully via SMTP to %s", recipients)
            return {
                "success": True,
                "provider": "smtp",
                "message": "Email sent successfully via SMTP",
            }
        except Exception as ex:
            logger.exception("Failed to send email via SMTP to %s: %s", recipients, ex)
            return {
                "success": False,
                "provider": "smtp",
                "error": str(ex),
                "message": f"Failed to send email via SMTP: {ex}",
            }

    @classmethod
    def send_email(
        cls,
        to: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main dispatch entry point:
        Prioritizes Resend REST API (HTTPS port 443) if RESEND_API_KEY is present;
        falls back to Flask-Mail SMTP if not.
        """
        api_key = cls.get_api_key()
        if api_key:
            return cls.send_via_resend_api(
                api_key=api_key,
                to=to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                sender=sender,
            )

        # Fallback to SMTP
        return cls.send_via_smtp(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            sender=sender,
        )

    # ── High-Level Workflow Methods ─────────────────────────────────

    @classmethod
    def send_verification_email(cls, user: Any, token: str) -> Dict[str, Any]:
        """Send email verification link to newly registered user."""
        try:
            verify_url = url_for("security.verify_email", token=token, _external=True)
        except RuntimeError:
            base = os.getenv("FRONTEND_URL", "http://localhost:5000")
            verify_url = f"{base}/security/verify/{token}"

        try:
            html = render_template(
                "emails/verify_email.html", user=user, verify_url=verify_url
            )
        except Exception:
            html = None

        text = (
            f"Welcome to eGrossary!\n\n"
            f"Please verify your email address by visiting this link:\n{verify_url}\n\n"
            f"If you did not create an account, please disregard this email."
        )

        return cls.send_email(
            to=user.email,
            subject="Verify Your Email | eGrossary",
            html_content=html,
            text_content=text,
        )

    @classmethod
    def send_password_reset_email(cls, user: Any, token: str) -> Dict[str, Any]:
        """Send password reset instructions with 15-minute token."""
        try:
            reset_url = url_for("security.reset_password", token=token, _external=True)
        except RuntimeError:
            base = os.getenv("FRONTEND_URL", "http://localhost:5000")
            reset_url = f"{base}/security/reset-password/{token}"

        try:
            html = render_template(
                "emails/reset_password.html", user=user, reset_url=reset_url
            )
        except Exception:
            html = None

        text = (
            f"Hello {getattr(user, 'full_name', '') or user.username},\n\n"
            f"We received a request to reset your password for your eGrossary account.\n"
            f"Click here to reset your password: {reset_url}\n\n"
            f"This link expires in 15 minutes. If you did not request this, please ignore this email."
        )

        return cls.send_email(
            to=user.email,
            subject="Password Reset Request | eGrossary",
            html_content=html,
            text_content=text,
        )

    @classmethod
    def send_order_confirmation_email(cls, order: Any, user: Any) -> Dict[str, Any]:
        """Send order confirmation email upon successful checkout or payment."""
        recipient = getattr(user, "email", None)
        if not recipient:
            return {"success": False, "message": "User has no email address."}

        try:
            html = render_template(
                "emails/order_confirmation.html", order=order, user=user
            )
        except Exception:
            html = None

        text = (
            f"eGrossary Order Confirmation\n\n"
            f"Dear {getattr(user, 'full_name', '') or user.username},\n"
            f"Thank you for your order! Your order #{order.id} has been placed successfully.\n"
            f"Total Amount: ₹{order.total_amount}\n"
            f"Payment Method: {order.payment_method}\n"
        )

        return cls.send_email(
            to=recipient,
            subject=f"Order Confirmation - #{order.id} | eGrossary",
            html_content=html,
            text_content=text,
        )

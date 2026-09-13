import base64
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
    4. Base64 & byte attachments (e.g. PDF Tax Invoices).
    5. Complete 7-stage e-grocery customer notification sequence.
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
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Sends transactional email via Resend HTTPS REST API.
        Supports native base64 attachments.
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

        if attachments:
            formatted_attachments = []
            for att in attachments:
                fn = att.get("filename", "document.pdf")
                content = att.get("content")
                if isinstance(content, bytes):
                    content_str = base64.b64encode(content).decode("utf-8")
                elif isinstance(content, str):
                    content_str = content
                else:
                    continue
                formatted_attachments.append({
                    "filename": fn,
                    "content": content_str,
                })
            if formatted_attachments:
                payload["attachments"] = formatted_attachments

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
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Fallback to Flask-Mail SMTP with attachment support."""
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

            if attachments:
                for att in attachments:
                    fn = att.get("filename", "document.pdf")
                    ctype = att.get("type") or att.get("content_type", "application/pdf")
                    content = att.get("content")
                    if isinstance(content, str):
                        try:
                            raw_data = base64.b64decode(content)
                        except Exception:
                            raw_data = content.encode("utf-8")
                    elif isinstance(content, bytes):
                        raw_data = content
                    else:
                        continue
                    msg.attach(filename=fn, content_type=ctype, data=raw_data)

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
        attachments: Optional[List[Dict[str, Any]]] = None,
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
                attachments=attachments,
            )

        return cls.send_via_smtp(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            sender=sender,
            attachments=attachments,
        )

    # ── Helpers for E-Grocery Sequencing ────────────────────────────

    @classmethod
    def _resolve_user(cls, order: Any, user: Any = None) -> Optional[Any]:
        """Resolves User object from order relationship or database query."""
        if user is not None:
            return user
        if hasattr(order, 'user') and order.user is not None:
            return order.user
        if hasattr(order, 'user_id') and order.user_id:
            try:
                from database.models import db
                from database.models.user import User
                return db.session.get(User, order.user_id)
            except Exception:
                pass
        return None

    @classmethod
    def _get_site_urls(cls, order: Any = None) -> Dict[str, str]:
        """Calculates frontend & backend URLs for email CTAs."""
        frontend_base = "http://127.0.0.1:3000"
        backend_base = "http://127.0.0.1:5000"
        if current_app:
            frontend_base = (
                current_app.config.get("FRONTEND_URL")
                or current_app.config.get("BASE_URL")
                or frontend_base
            ).rstrip("/")
            backend_base = (
                current_app.config.get("BASE_URL")
                or backend_base
            ).rstrip("/")
        else:
            frontend_base = os.getenv("FRONTEND_URL", frontend_base).rstrip("/")
            backend_base = os.getenv("BASE_URL", backend_base).rstrip("/")

        order_id = getattr(order, "id", "") if order else ""
        return {
            "frontend_base": frontend_base,
            "backend_base": backend_base,
            "order_url": f"{frontend_base}/customer/orders.html",
            "order_confirmation_url": (
                f"{frontend_base}/customer/order-confirmation.html?order_id={order_id}"
                if order_id
                else f"{frontend_base}/customer/orders.html"
            ),
            "invoice_view_url": (
                f"{frontend_base}/customer/invoice.html?id={order_id}"
                if order_id
                else f"{frontend_base}/customer/orders.html"
            ),
            "invoice_pdf_url": (
                f"{backend_base}/api/orders/{order_id}/invoice"
                if order_id
                else "#"
            ),
            "review_url": f"{frontend_base}/customer/orders.html",
            "support_email": "support@egrossary.com",
        }

    @classmethod
    def _format_order_date(cls, order: Any) -> str:
        """Formats order creation timestamp safely."""
        created_at = getattr(order, "created_at", None)
        if hasattr(created_at, "strftime") and callable(created_at.strftime):
            try:
                formatted = created_at.strftime("%d %B %Y, %I:%M %p")
                if isinstance(formatted, str):
                    return formatted
            except Exception:
                pass
        return "Today"

    @classmethod
    def _calculate_pricing(cls, order: Any) -> Dict[str, Any]:
        """Calculates item pricing breakdown with delivery fee and discounts."""
        raw_items = getattr(order, "order_items", None)
        if isinstance(raw_items, (list, tuple)):
            items = raw_items
        elif hasattr(raw_items, "all") and callable(raw_items.all):
            items = raw_items.all()
        elif hasattr(raw_items, "__iter__") and type(raw_items).__name__ != "MagicMock":
            items = list(raw_items)
        else:
            items = []

        items_list = []
        subtotal = 0.0

        for it in items:
            try:
                pname = getattr(getattr(it, "product", None), "name", "Grocery Item") or "Grocery Item"
                qty = int(getattr(it, "quantity", 1) or 1)
                uprice = float(getattr(it, "price", 0.0) or 0.0)
                line_sub = float(getattr(it, "subtotal", uprice * qty) or (uprice * qty))
                subtotal += line_sub
                items_list.append({
                    "name": str(pname),
                    "quantity": qty,
                    "price": uprice,
                    "subtotal": line_sub,
                    "unit": getattr(getattr(it, "product", None), "unit", "pack") or "pack",
                })
            except Exception:
                continue

        try:
            order_total = float(getattr(order, "total_amount", 0.0) or 0.0)
        except (ValueError, TypeError):
            order_total = subtotal

        if subtotal == 0.0 and order_total > 0.0:
            subtotal = order_total

        delivery_fee = 0.0 if (order_total >= 500.0 or order_total == 0.0) else 30.0
        discount = max(0.0, round((subtotal + delivery_fee) - order_total, 2))

        return {
            "order_items": items_list,
            "items": items_list,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "discount": discount,
            "total": order_total,
        }

    # ── High-Level Auth Methods ─────────────────────────────────────

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

    # ── E-Grocery Customer Lifecycle Email Sequence ─────────────────

    @classmethod
    def send_order_confirmation_email(cls, order: Any, user: Any = None) -> Dict[str, Any]:
        """
        Stage 1: Order Confirmation (Sent immediately after checkout).
        Contains itemized grocery table, delivery address, 15-min delivery window, and pricing.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                logger.info("Order confirmation email skipped: No recipient email for order #%s", getattr(order, 'id', ''))
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)

            try:
                html = render_template(
                    "emails/order_confirmation.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering order_confirmation.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/order_confirmation.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Order Confirmed #EGM-{order.id}\n"
                    f"Total: INR {pricing['total']:.2f}\n"
                    f"Address: {getattr(order, 'shipping_address', 'Doorstep')}\n"
                    f"Track: {urls['order_confirmation_url']}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Order Confirmed #EGM-{order.id} — Your Grocery Order is Confirmed",
                html_content=html,
                text_content=text,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_order_confirmation_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

    @classmethod
    def send_payment_confirmation_email(
        cls, order: Any, user: Any = None, transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 2: Payment Confirmation / Receipt (Sent when payment is marked Paid).
        Contains amount, payment mode, transaction reference ID, and dark store prep status.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)

            try:
                html = render_template(
                    "emails/payment_confirmation.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    transaction_id=transaction_id,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering payment_confirmation.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/payment_confirmation.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    transaction_id=transaction_id,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Payment Received #EGM-{order.id}\n"
                    f"Amount Paid: INR {pricing['total']:.2f} via {order.payment_method}\n"
                    f"Ref: {transaction_id or f'TXN-EGM-{order.id}'}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Payment Received #EGM-{order.id} — ₹{pricing['total']:.2f} via {order.payment_method}",
                html_content=html,
                text_content=text,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_payment_confirmation_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

    @classmethod
    def send_order_packed_email(cls, order: Any, user: Any = None) -> Dict[str, Any]:
        """
        Stage 3: Order Packed (Sent when status changes to Packed).
        Contains packaging quality seal, hub picking confirmation, and dispatch countdown.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)

            try:
                html = render_template(
                    "emails/order_packed.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering order_packed.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/order_packed.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Order Packed #EGM-{order.id}\n"
                    f"All {len(pricing['order_items']) if pricing['order_items'] else 1} items have been sealed and quality inspected at our APMC Hub.\n"
                    f"Track: {urls['order_url']}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Order Packed #EGM-{order.id} — Fresh groceries sealed & ready",
                html_content=html,
                text_content=text,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_order_packed_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

    @classmethod
    def send_out_for_delivery_email(cls, order: Any, user: Any = None) -> Dict[str, Any]:
        """
        Stage 4: Out for Delivery (Sent when rider is dispatched).
        Contains live delivery status, estimated arrival (~15 mins), and doorstep details.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)

            try:
                html = render_template(
                    "emails/out_for_delivery.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering out_for_delivery.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/out_for_delivery.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Out for Delivery #EGM-{order.id}\n"
                    f"Your groceries are arriving in ~15 Minutes at {order.shipping_address}.\n"
                    f"Track: {urls['order_url']}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Out for Delivery #EGM-{order.id} — Arriving in ~15 Minutes!",
                html_content=html,
                text_content=text,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_out_for_delivery_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

    @classmethod
    def send_order_delivered_email(
        cls, order: Any, user: Any = None, attach_invoice: bool = True
    ) -> Dict[str, Any]:
        """
        Stage 5: Order Delivered + Tax Invoice & Review CTA (Sent upon delivery).
        Attaches the official ReportLab PDF tax invoice with GST breakdown and prompts product ratings.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)

            # Generate PDF Invoice attachment
            attachments = None
            if attach_invoice:
                try:
                    from backend.services.export_service import generate_order_invoice_pdf
                    pdf_bytes = generate_order_invoice_pdf(order)
                    if pdf_bytes:
                        attachments = [{
                            "filename": f"Tax-Invoice-EGM-{order.id:05d}.pdf",
                            "content": pdf_bytes,
                            "type": "application/pdf"
                        }]
                except Exception as pdf_err:
                    logger.warning("Could not generate invoice PDF attachment for order #%s: %s", getattr(order, 'id', ''), pdf_err)

            try:
                html = render_template(
                    "emails/order_delivered.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering order_delivered.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/order_delivered.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Delivered: Order #EGM-{order.id} + Tax Invoice\n"
                    f"Total Paid: INR {pricing['total']:.2f}\n"
                    f"Invoice attached as PDF. Rate your items at {urls['review_url']}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Delivered: Order #EGM-{order.id} + Your Tax Invoice & Receipt",
                html_content=html,
                text_content=text,
                attachments=attachments,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_order_delivered_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

    @classmethod
    def send_order_cancelled_email(
        cls, order: Any, user: Any = None, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 6: Order Cancellation (Sent when order is cancelled).
        Provides cancellation reason, stock restoration notice, and refund breakdown.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)

            try:
                html = render_template(
                    "emails/order_cancelled.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    reason=reason,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering order_cancelled.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/order_cancelled.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    reason=reason,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Order Cancelled #EGM-{order.id}\n"
                    f"Reason: {reason or 'Requested by customer'}\n"
                    f"Payment Status: {order.payment_status}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Order Cancelled #EGM-{order.id} — eGrossary Update",
                html_content=html,
                text_content=text,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_order_cancelled_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

    @classmethod
    def send_refund_confirmation_email(
        cls,
        order: Any,
        user: Any = None,
        refund_amount: Optional[float] = None,
        ref_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stage 7: Refund Confirmation (Sent when payment status transitions to Refunded).
        Provides refunded amount, bank reference number, and expected settlement window.
        """
        try:
            resolved_user = cls._resolve_user(order, user)
            recipient = getattr(resolved_user, "email", None)
            if not recipient:
                return {"success": False, "message": "User has no email address."}

            pricing = cls._calculate_pricing(order)
            urls = cls._get_site_urls(order)
            order_date = cls._format_order_date(order)
            ref_amount = float(refund_amount if refund_amount is not None else pricing["total"])

            try:
                html = render_template(
                    "emails/refund_confirmation.html",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    refund_amount=ref_amount,
                    ref_id=ref_id,
                    order_date=order_date,
                )
            except Exception as render_err:
                logger.warning("Failed rendering refund_confirmation.html: %s", render_err)
                html = None

            try:
                text = render_template(
                    "emails/refund_confirmation.txt",
                    order=order,
                    user=resolved_user,
                    pricing=pricing,
                    urls=urls,
                    refund_amount=ref_amount,
                    ref_id=ref_id,
                    order_date=order_date,
                )
            except Exception:
                text = (
                    f"Refund Processed #EGM-{order.id}\n"
                    f"Amount: INR {ref_amount:.2f}\n"
                    f"Ref: {ref_id or f'REF-EGM-{order.id}'}"
                )

            return cls.send_email(
                to=recipient,
                subject=f"Refund Processed #EGM-{order.id} — ₹{ref_amount:.2f} credited back",
                html_content=html,
                text_content=text,
            )
        except Exception as ex:
            logger.exception("Unexpected error in send_refund_confirmation_email for order #%s: %s", getattr(order, 'id', ''), ex)
            return {"success": False, "error": str(ex)}

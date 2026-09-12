import json
from unittest.mock import MagicMock, patch
import pytest

from backend.services.email_service import EmailService


class MockResponse:
    def __init__(self, data, status=200):
        self._data = json.dumps(data).encode("utf-8")
        self.status = status

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_email_service_configured(app):
    with app.app_context():
        app.config["RESEND_API_KEY"] = "re_test_12345"
        assert EmailService.is_configured() is True
        assert EmailService.get_api_key() == "re_test_12345"


def test_email_service_not_configured(app):
    with app.app_context():
        app.config["RESEND_API_KEY"] = None
        app.config["MAIL_USERNAME"] = None
        with patch.dict("os.environ", {}, clear=True):
            assert EmailService.get_api_key() is None


def test_send_via_resend_api_success(app):
    with app.app_context():
        mock_resp = MockResponse({"id": "resend_msg_123"})
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = EmailService.send_via_resend_api(
                api_key="re_test_key",
                to="delivered@resend.dev",
                subject="Test Order Confirmed",
                html_content="<p>Order Placed</p>",
            )

        assert result["success"] is True
        assert result["provider"] == "resend_api"
        assert result["id"] == "resend_msg_123"


def test_send_via_resend_api_sandbox_restriction(app):
    with app.app_context():
        import urllib.error

        error_body = json.dumps(
            {
                "statusCode": 403,
                "message": "You can only send testing emails to your own email address (owner@example.com).",
                "name": "validation_error",
            }
        ).encode("utf-8")

        mock_err = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=MagicMock(read=lambda: error_body),
        )

        with patch("urllib.request.urlopen", side_effect=mock_err):
            result = EmailService.send_via_resend_api(
                api_key="re_test_key",
                to="customer@otherdomain.com",
                subject="Test",
            )

        assert result["success"] is False
        assert result["is_sandbox_restriction"] is True
        assert "sandbox restriction" in result["message"].lower()


def test_send_via_smtp_fallback(app):
    with app.app_context():
        app.config["RESEND_API_KEY"] = None
        with patch("backend.extensions.mail.send") as mock_mail_send:
            result = EmailService.send_via_smtp(
                to="customer@example.com",
                subject="SMTP Subject",
                html_content="<p>Hello SMTP</p>",
            )
            assert result["success"] is True
            assert result["provider"] == "smtp"
            assert mock_mail_send.called


def test_send_verification_email_renders_template(app):
    with app.app_context():
        user = MagicMock()
        user.email = "testuser@example.com"
        user.full_name = "Test User"
        user.username = "testuser"

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            result = EmailService.send_verification_email(user, "test_token_abc")

            assert result["success"] is True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["to"] == "testuser@example.com"
            assert "Verify Your Email" in call_kwargs["subject"]
            assert "test_token_abc" in call_kwargs["html_content"]
            assert "Verify Email Address" in call_kwargs["html_content"]


def test_send_password_reset_email_renders_template(app):
    with app.app_context():
        user = MagicMock()
        user.email = "testuser@example.com"
        user.full_name = "Test User"
        user.username = "testuser"

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            result = EmailService.send_password_reset_email(user, "reset_token_xyz")

            assert result["success"] is True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["to"] == "testuser@example.com"
            assert "Password Reset" in call_kwargs["subject"]
            assert "reset_token_xyz" in call_kwargs["html_content"]
            assert "15 minutes" in call_kwargs["html_content"]


def test_send_order_confirmation_email_renders_template(app):
    with app.app_context():
        user = MagicMock()
        user.email = "testuser@example.com"
        user.full_name = "Test User"
        user.username = "testuser"

        order = MagicMock()
        order.id = 999
        order.total_amount = 450.00
        order.payment_method = "COD"

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            result = EmailService.send_order_confirmation_email(order, user)

            assert result["success"] is True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["to"] == "testuser@example.com"
            assert "#999" in call_kwargs["subject"]
            assert "450.00" in call_kwargs["html_content"]
            assert "COD" in call_kwargs["html_content"]


def test_registration_with_resend_sandbox_auto_verifies(client, session):
    with patch.object(EmailService, "send_verification_email") as mock_send:
        mock_send.return_value = {
            "success": False,
            "is_sandbox_restriction": True,
            "message": "Resend test sandbox restriction"
        }

        resp = client.post("/auth/register", json={
            "username": "sandboxtester",
            "email": "external_dev@gmail.com",
            "password": "StrongPassword@2026",
            "full_name": "Sandbox Tester"
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "Registration successful" in data["message"]


def test_forgot_password_dispatches_email_service(client, session):
    from database.models import User
    from werkzeug.security import generate_password_hash

    user = User(
        username="resetuser",
        email="resetuser@gmail.com",
        password_hash=generate_password_hash("OldPass@123"),
        role="customer",
        is_verified=True
    )
    session.add(user)
    session.commit()

    with patch.object(EmailService, "send_password_reset_email") as mock_send:
        mock_send.return_value = {"success": True}

        resp = client.post("/security/forgot-password", json={
            "email": "resetuser@gmail.com"
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_send.assert_called_once()


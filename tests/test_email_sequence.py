"""Comprehensive tests for E-Grocery Customer Lifecycle Email Sequence & Tax Invoice Generation."""
import io
from unittest.mock import MagicMock, patch
import pytest

from backend.services.email_service import EmailService
from backend.services.export_service import generate_order_invoice_pdf
from backend.constants import OrderStatus, PaymentStatus


class DummyProduct:
    def __init__(self, name="Fresh Milk 1L", price=60.0, unit="1L"):
        self.name = name
        self.selling_price = price
        self.cost_price = price * 0.7
        self.unit = unit
        self.category = "Dairy"
        self.category_rel = None


class DummyOrderItem:
    def __init__(self, product, quantity=2, price=60.0):
        self.product = product
        self.quantity = quantity
        self.price = price
        self.profit = (price - (product.cost_price if product else 40.0)) * quantity

    @property
    def subtotal(self):
        return self.price * self.quantity


class DummyUser:
    def __init__(self, full_name="Akshay Kumar", username="akshay", email="akshay@example.com"):
        self.id = 101
        self.full_name = full_name
        self.username = username
        self.email = email
        self.phone = "+91 98765 43210"


class DummyOrder:
    def __init__(self, id=10452, total=560.0, status="Pending", payment_method="UPI", payment_status="Paid"):
        self.id = id
        self.user_id = 101
        self.total_amount = total
        self.order_status = status
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.shipping_address = "Flat 402, Sunshine Heights, Sector 15, Vashi, Navi Mumbai, 400703"
        self.created_at = None
        self.user = DummyUser()
        
        prod_milk = DummyProduct("Milk 1L", 60.0, "1L")
        prod_rice = DummyProduct("Rice 5kg", 320.0, "5kg")
        prod_apples = DummyProduct("Apples 1kg", 140.0, "1kg")
        
        self.order_items = [
            DummyOrderItem(prod_milk, quantity=2, price=60.0),
            DummyOrderItem(prod_rice, quantity=1, price=320.0),
            DummyOrderItem(prod_apples, quantity=1, price=140.0),
        ]


# ── Stage 1: Order Confirmation ──────────────────────────────────────

def test_order_confirmation_renders_itemized_table_and_eta(app):
    """Verify Order Confirmation email renders items, quantities, subtotal, delivery fee, and 15-min ETA."""
    with app.app_context():
        order = DummyOrder(id=10452, total=560.0)
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_order_confirmation_email(order, user)

            assert res["success"] is True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]

            assert call_kwargs["to"] == "akshay@example.com"
            assert "Order Confirmed #EGM-10452" in call_kwargs["subject"]

            html = call_kwargs["html_content"]
            assert "Milk 1L" in html
            assert "Rice 5kg" in html
            assert "Apples 1kg" in html
            assert "₹120.00" in html
            assert "560.00" in html
            assert "Sunshine Heights" in html
            assert "15–20 minutes" in html

            text = call_kwargs["text_content"]
            assert "Order #EGM-10452" in text
            assert "Milk 1L" in text
            assert "Total" in text
            assert "15–20 minutes" in text


# ── Stage 2: Payment Confirmation ────────────────────────────────────

def test_payment_confirmation_renders_receipt(app):
    """Verify Payment Confirmation / Receipt renders payment method, amount, and reference ID."""
    with app.app_context():
        order = DummyOrder(id=10452, total=560.0, payment_method="UPI")
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_payment_confirmation_email(order, user, transaction_id="UPI-IND-987654321")

            assert res["success"] is True
            call_kwargs = mock_send.call_args[1]

            assert "Payment Received #EGM-10452" in call_kwargs["subject"]
            assert "₹560.00" in call_kwargs["subject"]
            assert "UPI-IND-987654321" in call_kwargs["html_content"]
            assert "UPI" in call_kwargs["html_content"]
            assert "560.00" in call_kwargs["html_content"]


# ── Stage 3: Order Packed ────────────────────────────────────────────

def test_order_packed_renders_hub_seal(app):
    """Verify Order Packed email renders packing verification badge and APMC dark store notice."""
    with app.app_context():
        order = DummyOrder(id=10452, status="Packed")
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_order_packed_email(order, user)

            assert res["success"] is True
            call_kwargs = mock_send.call_args[1]

            assert "Order Packed #EGM-10452" in call_kwargs["subject"]
            assert "Fresh groceries sealed & ready" in call_kwargs["subject"]
            assert "Quality Checked" in call_kwargs["html_content"]
            assert "3 item(s)" in call_kwargs["html_content"]


# ── Stage 4: Out for Delivery ────────────────────────────────────────

def test_out_for_delivery_renders_eta_and_address(app):
    """Verify Out for Delivery email renders ~15 min express arrival and destination address."""
    with app.app_context():
        order = DummyOrder(id=10452, status="Out for Delivery")
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_out_for_delivery_email(order, user)

            assert res["success"] is True
            call_kwargs = mock_send.call_args[1]

            assert "Out for Delivery #EGM-10452" in call_kwargs["subject"]
            assert "~15 Minutes" in call_kwargs["html_content"]
            assert "Sunshine Heights" in call_kwargs["html_content"]
            assert "Already Paid Online" in call_kwargs["html_content"]


# ── Stage 5: Order Delivered + Tax Invoice PDF & Review CTA ───────────

def test_order_delivered_attaches_pdf_tax_invoice_and_review_cta(app):
    """Verify Order Delivered email attaches official PDF invoice and includes Rate & Review CTA."""
    with app.app_context():
        order = DummyOrder(id=10452, status="Delivered")
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_order_delivered_email(order, user, attach_invoice=True)

            assert res["success"] is True
            call_kwargs = mock_send.call_args[1]

            assert "Delivered: Order #EGM-10452 + Your Tax Invoice & Receipt" in call_kwargs["subject"]
            html = call_kwargs["html_content"]
            assert "Rate &amp; Review Products" in html or "Rate & Review" in html
            assert "INV-EGM-10452" in html
            assert "27AABCE1234F1Z5" in html  # GSTIN

            # Check PDF attachment
            attachments = call_kwargs.get("attachments")
            assert attachments is not None
            assert len(attachments) == 1
            att = attachments[0]
            assert att["filename"] == "Tax-Invoice-EGM-10452.pdf"
            assert att["type"] == "application/pdf"
            assert len(att["content"]) > 100  # valid PDF binary


def test_generate_order_invoice_pdf_creates_valid_gst_invoice():
    """Verify ReportLab PDF generation creates valid PDF with GST and item data."""
    order = DummyOrder(id=10452, total=560.0)
    pdf_bytes = generate_order_invoice_pdf(order)

    assert pdf_bytes is not None
    assert pdf_bytes.startswith(b"%PDF-")  # Valid PDF header
    assert len(pdf_bytes) > 500


# ── Stage 6: Order Cancelled ─────────────────────────────────────────

def test_order_cancelled_renders_reason_and_refund_status(app):
    """Verify Order Cancelled email renders cancellation notice, stock restoration, and refund details."""
    with app.app_context():
        order = DummyOrder(id=10452, status="Cancelled", payment_status="Paid")
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_order_cancelled_email(
                order, user, reason="Customer requested doorstep delivery reschedule"
            )

            assert res["success"] is True
            call_kwargs = mock_send.call_args[1]

            assert "Order Cancelled #EGM-10452" in call_kwargs["subject"]
            html = call_kwargs["html_content"]
            assert "doorstep delivery reschedule" in html
            assert "3 to 5 business days" in html
            assert "560.00" in html


# ── Stage 7: Refund Confirmation ─────────────────────────────────────

def test_refund_confirmation_renders_reference_and_timeline(app):
    """Verify Refund Processed email renders refund amount, reference number, and bank timeline."""
    with app.app_context():
        order = DummyOrder(id=10452, total=560.0)
        user = order.user

        with patch.object(EmailService, "send_email") as mock_send:
            mock_send.return_value = {"success": True}
            res = EmailService.send_refund_confirmation_email(
                order, user, refund_amount=560.0, ref_id="REF-EGM-10452-BANK99"
            )

            assert res["success"] is True
            call_kwargs = mock_send.call_args[1]

            assert "Refund Processed #EGM-10452" in call_kwargs["subject"]
            assert "₹560.00" in call_kwargs["subject"]
            html = call_kwargs["html_content"]
            assert "REF-EGM-10452-BANK99" in html
            assert "3 to 5 business days" in html
            assert "560.00" in html


# ── Robustness & Fault Tolerance ─────────────────────────────────────

def test_email_service_fault_tolerance(app):
    """Verify that email service never raises exceptions on transport failure."""
    with app.app_context():
        order = DummyOrder(id=10452)
        user = order.user

        with patch.object(EmailService, "send_email", side_effect=RuntimeError("SMTP Transport Timeout")):
            # Should not raise exception
            res = EmailService.send_order_confirmation_email(order, user)
            assert res["success"] is False
            assert "error" in res


def test_admin_order_status_transitions_trigger_emails(client, session):
    """Verify updating order status through admin route triggers corresponding email method."""
    from backend.models.user import User
    from backend.models.order import Order
    from werkzeug.security import generate_password_hash

    # Create admin and customer
    admin = User(username="admin_seq", email="admin_seq@example.com", password_hash=generate_password_hash("AdminPass@123"), role="admin", is_verified=True)
    customer = User(username="cust_seq", email="cust_seq@example.com", password_hash=generate_password_hash("CustPass@123"), role="customer", is_verified=True)
    session.add_all([admin, customer])
    session.commit()

    order = Order(
        user_id=customer.id,
        total_amount=350.0,
        payment_method="UPI",
        payment_status="Pending",
        order_status="Pending",
        shipping_address="Shop 12, APMC Sector 19",
    )
    session.add(order)
    session.commit()

    # Login as admin
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin.id)
        sess["_fresh"] = True

    # 1. Transition Pending -> Packed (Triggers send_order_packed_email)
    with patch.object(EmailService, "send_order_packed_email") as mock_packed:
        resp = client.post(f"/admin/orders/{order.id}/update-status", json={"order_status": "Packed"})
        assert resp.status_code == 200
        mock_packed.assert_called_once()

    # 2. Transition Packed -> Out for Delivery (Triggers send_out_for_delivery_email)
    with patch.object(EmailService, "send_out_for_delivery_email") as mock_out:
        resp = client.post(f"/admin/orders/{order.id}/update-status", json={"order_status": "Out for Delivery"})
        assert resp.status_code == 200
        mock_out.assert_called_once()

    # 3. Transition Out for Delivery -> Delivered (Triggers send_order_delivered_email)
    with patch.object(EmailService, "send_order_delivered_email") as mock_deliv:
        resp = client.post(f"/admin/orders/{order.id}/update-status", json={"order_status": "Delivered", "payment_status": "Paid"})
        assert resp.status_code == 200
        mock_deliv.assert_called_once()

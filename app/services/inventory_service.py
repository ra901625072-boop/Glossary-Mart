"""
InventoryService — Centralized, race-condition-safe stock management.

All stock mutations (sales, purchases, cancellations, returns) MUST go
through this service to ensure:
  1. Row-level locking (with_for_update) prevents overselling.
  2. Every change is logged to ActivityLog for audit trails.
  3. Low-stock notifications are generated automatically.
"""

import json

from flask_login import current_user

from app.models import db
from app.models.user import ActivityLog
from app.models.promotion import Notification
from app.models.product import Product


class InventoryService:

    # ------------------------------------------------------------------ #
    #  Public Interface
    # ------------------------------------------------------------------ #

    @staticmethod
    def deduct_stock(product_id: int, quantity: int, triggered_by: str = "sale") -> tuple[bool, str]:
        """
        Atomically deduct stock. Returns (success, message).
        Uses SELECT … FOR UPDATE to serialize concurrent requests.
        """
        try:
            product = (
                db.session.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )

            if not product:
                return False, f"Product #{product_id} not found."

            if product.stock_quantity < quantity:
                return False, (
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.stock_quantity}, Requested: {quantity}."
                )

            product.stock_quantity -= quantity

            # Audit log
            InventoryService._log(
                action="DEDUCT_STOCK",
                entity_type="Product",
                entity_id=product_id,
                details=json.dumps({
                    "product": product.name,
                    "qty_deducted": quantity,
                    "new_stock": product.stock_quantity,
                    "trigger": triggered_by,
                }),
            )

            # Low-stock alert
            if product.stock_quantity <= product.minimum_stock_alert:
                InventoryService._notify_low_stock(product)

            return True, "Stock updated."

        except Exception as e:
            db.session.rollback()
            return False, f"Stock update error: {str(e)}"

    @staticmethod
    def add_stock(product_id: int, quantity: int, triggered_by: str = "purchase") -> tuple[bool, str]:
        """
        Atomically add stock (e.g. after a purchase / cancellation restoral).
        """
        try:
            product = (
                db.session.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )

            if not product:
                return False, f"Product #{product_id} not found."

            product.stock_quantity += quantity

            InventoryService._log(
                action="ADD_STOCK",
                entity_type="Product",
                entity_id=product_id,
                details=json.dumps({
                    "product": product.name,
                    "qty_added": quantity,
                    "new_stock": product.stock_quantity,
                    "trigger": triggered_by,
                }),
            )

            return True, "Stock restocked."

        except Exception as e:
            db.session.rollback()
            return False, f"Stock restock error: {str(e)}"

    @staticmethod
    def restore_order_stock(order) -> None:
        """
        Restore stock for all items in a cancelled/returned order.
        Safe to call multiple times — idempotency is the caller's responsibility.
        """
        for item in order.order_items:
            if item.product:
                InventoryService.add_stock(
                    item.product_id,
                    item.quantity,
                    triggered_by=f"order_cancel#{order.id}",
                )

    # ------------------------------------------------------------------ #
    #  Internal Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _log(action: str, entity_type: str, entity_id: int, details: str) -> None:
        """Persist an ActivityLog entry (does NOT commit — caller must commit)."""
        from flask import request as flask_request

        try:
            ip = flask_request.remote_addr
        except RuntimeError:
            ip = None

        log = ActivityLog(
            user_id=current_user.id if current_user and current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip,
        )
        db.session.add(log)

    @staticmethod
    def _notify_low_stock(product: Product) -> None:
        """Create a low-stock admin notification (does NOT commit)."""
        # Avoid duplicate notifications: check if an unread one already exists
        existing = db.session.query(Notification).filter_by(
            notif_type="warning",
            is_read=False,
            link=f"/admin/products/edit/{product.id}",
        ).first()

        if not existing:
            notif = Notification(
                user_id=None,  # Broadcast to all admins
                title="Low Stock Alert",
                message=(
                    f"'{product.name}' is running low — only "
                    f"{product.stock_quantity} unit(s) left "
                    f"(threshold: {product.minimum_stock_alert})."
                ),
                notif_type="warning",
                link=f"/admin/products/edit/{product.id}",
            )
            db.session.add(notif)

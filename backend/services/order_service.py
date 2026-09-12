from decimal import Decimal

from flask_login import current_user

from database.models import db
from database.models.order import Cart, Order, OrderItem
from database.models.promotion import Notification
from database.models.product import Product
from backend.services.inventory_service import InventoryService


class OrderService:
    @staticmethod
    def process_checkout(cart_items, shipping_address, payment_method):
        total_amount = sum(item.subtotal for item in cart_items)

        if payment_method == 'UDHAR':
            current_credit = float(getattr(current_user, 'credit', 0) or 0)
            if not getattr(current_user, 'is_verified', True) or (current_credit + float(total_amount)) > 5000:
                return False, None, 'Store credit (Udhar) limit exceeded or account not verified.'

        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status='Pending',
            order_status='Pending',
            shipping_address=shipping_address,
        )
        db.session.add(order)
        db.session.flush()  # Get order.id before looping items

        for item in cart_items:
            # Use InventoryService for atomic, row-locked stock deduction
            ok, msg = InventoryService.deduct_stock(
                item.product_id, item.quantity, triggered_by=f'order#{order.id}'
            )
            if not ok:
                db.session.rollback()
                return False, order, msg

            product = db.session.get(Product, item.product_id)
            profit = (product.selling_price - product.cost_price) * item.quantity
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.selling_price,
                profit=profit,
            )
            db.session.add(order_item)

        # Clear DB cart for authenticated users
        if current_user.is_authenticated:
            db.session.query(Cart).filter_by(user_id=current_user.id).delete()

        # Broadcast admin notification for new order
        customer_name = current_user.full_name or current_user.username
        db.session.add(Notification(
            user_id=None,
            title="New Order Received",
            message=(
                f"Order #{order.id} placed by {customer_name} "
                f"({payment_method}) — ₹{float(total_amount):,.2f}"
            ),
            notif_type="info",
            link=f"/admin/orders/{order.id}",
        ))

        db.session.commit()

        if payment_method == 'UDHAR':
            current_user.credit = (
                Decimal(str(current_user.credit or 0)) + Decimal(str(total_amount))
            )
            db.session.commit()

        return True, order, 'Order processed successfully.'

    @staticmethod
    def create_order_from_cart(user_id: int, shipping_address: str, payment_method: str = 'COD'):
        """Create order directly from user's database cart with validation."""
        cart_items = db.session.query(Cart).filter_by(user_id=user_id).all()
        if not cart_items:
            return None, 'Shopping cart is empty.'

        valid_methods = {'COD', 'UPI', 'CARD', 'UDHAR'}
        clean_method = str(payment_method or 'COD').strip().upper()
        if clean_method not in valid_methods:
            return None, 'Invalid payment method.'

        from database.models.user import User
        user = db.session.get(User, user_id)
        if not user:
            return None, 'User not found.'

        total_amount = sum(item.subtotal for item in cart_items)
        if total_amount <= 0:
            return None, 'Invalid order total amount.'

        if clean_method == 'UDHAR':
            current_credit = float(getattr(user, 'credit', 0) or 0)
            if not getattr(user, 'is_verified', True) or (current_credit + float(total_amount)) > 5000:
                return None, 'Store credit (Udhar) limit exceeded or account not verified.'

        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            payment_method=clean_method,
            payment_status='Pending',
            order_status='Pending',
            shipping_address=shipping_address,
        )
        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            ok, msg = InventoryService.deduct_stock(
                item.product_id, item.quantity, triggered_by=f'order#{order.id}'
            )
            if not ok:
                db.session.rollback()
                return None, msg

            product = db.session.get(Product, item.product_id)
            profit = (product.selling_price - product.cost_price) * item.quantity
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.selling_price,
                profit=profit,
            )
            db.session.add(order_item)

        # Clear cart
        db.session.query(Cart).filter_by(user_id=user_id).delete()

        # Admin broadcast notification
        customer_name = user.full_name or user.username
        db.session.add(Notification(
            user_id=None,
            title="New Order Received",
            message=(
                f"Order #{order.id} placed by {customer_name} "
                f"({clean_method}) — ₹{float(total_amount):,.2f}"
            ),
            notif_type="info",
            link=f"/admin/orders/{order.id}",
        ))

        if clean_method == 'UDHAR':
            user.credit = Decimal(str(user.credit or 0)) + Decimal(str(total_amount))

        try:
            db.session.commit()
            return order, 'Order created successfully.'
        except Exception:
            db.session.rollback()
            return None, 'Database error completing order checkout.'

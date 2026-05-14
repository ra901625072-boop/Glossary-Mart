from decimal import Decimal

from flask_login import current_user

from app.models import db
from app.models.order import Cart, Order, OrderItem
from app.models.promotion import Notification
from app.models.product import Product
from app.services.inventory_service import InventoryService


class OrderService:
    @staticmethod
    def process_checkout(cart_items, shipping_address, payment_method):
        total_amount = sum(item.subtotal for item in cart_items)

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

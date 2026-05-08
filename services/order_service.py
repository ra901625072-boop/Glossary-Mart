from decimal import Decimal
from flask_login import current_user
from models import Cart, Order, OrderItem, Product, db

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
            shipping_address=shipping_address
        )
        db.session.add(order)
        db.session.flush()
        
        for item in cart_items:
            # Atomic stock reduction
            rows_affected = db.session.query(Product).filter(
                Product.id == item.product_id,
                Product.stock_quantity >= item.quantity
            ).update({
                Product.stock_quantity: Product.stock_quantity - item.quantity
            }, synchronize_session=False)

            if rows_affected == 0:
                db.session.rollback()
                return False, order, f'Insufficient stock for an item during processing.'

            product = db.session.get(Product, item.product_id)
            profit = (product.selling_price - product.cost_price) * item.quantity
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.selling_price,
                profit=profit
            )
            db.session.add(order_item)
        
        # Clear cart for DB users
        if current_user.is_authenticated:
            db.session.query(Cart).filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        
        if payment_method == 'UDHAR':
            # Use Decimal for accurate currency addition
            current_user.credit = Decimal(str(current_user.credit or 0)) + Decimal(str(total_amount))
            db.session.commit()
            
        return True, order, 'Order processed successfully.'

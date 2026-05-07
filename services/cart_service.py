from flask import session
from flask_login import current_user

from models import Cart, Product, db


class CartService:
    @staticmethod
    def get_cart_items():
        if current_user.is_authenticated and current_user.role == 'customer':
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            total = sum(item.subtotal for item in cart_items)
            return cart_items, total
        else:
            cart = session.get('cart', {})
            cart_items = []
            total = 0
            
            class DummyCartItem:
                def __init__(self, p, q, pid):
                    self.product = p
                    self.quantity = q
                    self.id = "session_" + pid
                    self.subtotal = p.selling_price * q
                    self.product_id = p.id
                    
            for pid_str, qty in cart.items():
                product = Product.query.get(int(pid_str))
                if product:
                    item = DummyCartItem(product, qty, pid_str)
                    cart_items.append(item)
                    total += item.subtotal
            return cart_items, total

    @staticmethod
    def add_item(product_id, quantity):
        if quantity <= 0:
            return False, 'Invalid quantity.'
        
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return False, 'Product not found.'
            
        if product.stock_quantity < quantity:
            return False, f'Only {product.stock_quantity} units available.'
        
        if current_user.is_authenticated and current_user.role == 'customer':
            cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            if cart_item:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > product.stock_quantity:
                    return False, f'Cannot add more. Only {product.stock_quantity} units available.'
                cart_item.quantity = new_quantity
            else:
                cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)
            db.session.commit()
            return True, f'{product.name} added to cart!'
        else:
            if 'cart' not in session:
                session['cart'] = {}
            str_id = str(product_id)
            cart = session['cart']
            if str_id in cart:
                new_q = cart[str_id] + quantity
                if new_q > product.stock_quantity:
                    return False, f'Cannot add more. Only {product.stock_quantity} units available.'
                cart[str_id] = new_q
            else:
                cart[str_id] = quantity
            session.modified = True
            return True, f'{product.name} added to cart!'

    @staticmethod
    def update_item(cart_id, quantity):
        if current_user.is_authenticated and current_user.role == 'customer':
            cart_item = Cart.query.get(int(cart_id))
            if not cart_item or cart_item.user_id != current_user.id:
                return False, 'Unauthorized access.'
            
            if quantity <= 0:
                db.session.delete(cart_item)
                db.session.commit()
                return True, 'Item removed from cart.'
            
            if quantity > cart_item.product.stock_quantity:
                return False, f'Only {cart_item.product.stock_quantity} units available.'
            
            cart_item.quantity = quantity
            db.session.commit()
            return True, 'Cart updated.'
        else:
            pid = str(cart_id).replace('session_', '')
            cart = session.get('cart', {})
            if pid in cart:
                product = Product.query.get(int(pid))
                if not product or quantity <= 0:
                    del cart[pid]
                    session.modified = True
                    return True, 'Item removed from cart.'
                elif quantity > product.stock_quantity:
                    return False, f'Only {product.stock_quantity} units available.'
                else:
                    cart[pid] = quantity
                    session.modified = True
                    return True, 'Cart updated.'
            return False, 'Item not found in cart.'

    @staticmethod
    def remove_item(cart_id):
        if current_user.is_authenticated and current_user.role == 'customer':
            cart_item = Cart.query.get(int(cart_id))
            if not cart_item or cart_item.user_id != current_user.id:
                return False, 'Unauthorized access.'
            product_name = cart_item.product.name if cart_item.product else 'Item'
            db.session.delete(cart_item)
            db.session.commit()
            return True, f'{product_name} removed from cart.'
        else:
            pid = str(cart_id).replace('session_', '')
            cart = session.get('cart', {})
            if pid in cart:
                product = Product.query.get(int(pid))
                product_name = product.name if product else 'Item'
                del cart[pid]
                session.modified = True
                return True, f'{product_name} removed from cart.'
            return False, 'Item not found in cart.'

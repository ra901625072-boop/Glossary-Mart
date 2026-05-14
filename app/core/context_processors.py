from flask import session
from flask_login import current_user
from app.models import db, Cart

def init_context_processors(app):
    """Register context processors"""
    
    @app.context_processor
    def inject_cart_count():
        """Make cart count available in all templates"""
        cart_count = 0
        try:
            if current_user.is_authenticated and current_user.role == 'customer':
                cart_count = db.session.query(Cart).filter_by(user_id=current_user.id).count()
            elif not current_user.is_authenticated:
                cart_count = len(session.get('cart', {}))
        except Exception:
            cart_count = 0
        return {'cart_count': cart_count}

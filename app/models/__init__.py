from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models to register them with SQLAlchemy
from .user import User, ActivityLog
from .product import Product, Category, Review, Sale
from .order import Order, OrderItem, Cart, Wishlist
from .inventory import Supplier, Purchase
from .promotion import Coupon, Notification

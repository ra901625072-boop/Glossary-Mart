"""
e Grossary - Production Data Sanitizer (clean_dummy_data.py)
Purges all simulated/dummy operational transactions (orders, sales, purchases,
fake customer accounts, reviews, and activity logs) while preserving clean
master catalog data (categories, products, suppliers, coupons, and admin account).
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend import create_app
from database.models import db
from database.models.order import Order, OrderItem
from database.models.product import Category, Product, Review, Sale
from database.models.inventory import Purchase, Supplier
from database.models.promotion import Coupon
from database.models.user import ActivityLog, User


def clean_database():
    """Purge simulated transactions and dummy accounts."""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print(" E GROSSARY - PRODUCTION DATA SANITIZER")
        print("=" * 60)
        print(f" Target Database: {db.engine.url}\n")

        # 1. Purge Orders & Order Items
        num_items = OrderItem.query.delete()
        num_orders = Order.query.delete()
        print(f" [*] Deleted {num_orders} dummy orders and {num_items} order items.")

        # 2. Purge Simulated POS Counter Sales
        num_sales = Sale.query.delete()
        print(f" [*] Deleted {num_sales} dummy counter POS sales.")

        # 3. Purge Simulated Inventory Purchases
        num_purchases = Purchase.query.delete()
        print(f" [*] Deleted {num_purchases} dummy vendor purchase orders.")

        # 4. Purge Simulated Product Reviews
        num_reviews = Review.query.delete()
        print(f" [*] Deleted {num_reviews} dummy product reviews.")

        # 5. Purge Dummy Customer Accounts (Keep only Admin)
        dummy_users = User.query.filter(User.role != 'admin').all()
        num_users = len(dummy_users)
        for u in dummy_users:
            db.session.delete(u)
        print(f" [*] Deleted {num_users} dummy customer accounts (Admin account preserved).")

        # 6. Purge Audit Activity Logs
        num_logs = ActivityLog.query.delete()
        print(f" [*] Deleted {num_logs} dummy activity logs.")

        # 7. Reset Coupon Usage Statistics
        coupons = Coupon.query.all()
        for c in coupons:
            c.times_used = 0
        print(f" [*] Reset usage count to 0 for {len(coupons)} master coupons.")

        db.session.commit()

        print("\n" + "-" * 60)
        print(" POST-CLEANUP VERIFICATION")
        print("-" * 60)
        print(f" Categories: {Category.query.count()} (Preserved)")
        print(f" Products:   {Product.query.count()} (Preserved)")
        print(f" Suppliers:  {Supplier.query.count()} (Preserved)")
        print(f" Coupons:    {Coupon.query.count()} (Preserved, all times_used=0)")
        print(f" Users:      {User.query.count()} (Only admin: {[u.username for u in User.query.all()]})")
        print(f" Orders:     {Order.query.count()}")
        print(f" Sales:      {Sale.query.count()}")
        print(f" Purchases:  {Purchase.query.count()}")
        print(f" Reviews:    {Review.query.count()}")
        print("=" * 60)
        print(" Production database sanitization completed successfully!\n")


if __name__ == '__main__':
    clean_database()

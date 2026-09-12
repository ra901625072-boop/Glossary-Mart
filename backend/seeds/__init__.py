"""
Seed orchestrator for e Grossary.
Loads all authentic FMCG categories, products, suppliers, purchases, coupons,
customer profiles, historical orders, and counter POS sales into the database.
"""


def seed_all(app):
    """Orchestrate all seeding in proper dependency order."""
    from .categories import seed_categories
    from .products import seed_products
    from .suppliers import seed_suppliers
    from .purchases import seed_purchases
    from .coupons import seed_coupons
    from .users import create_admin, create_customer
    from .orders_and_sales import seed_orders_and_sales

    # 1. Base Master Catalog
    cat_map = seed_categories()
    seed_products(cat_map)

    # 2. Suppliers & Inward Stocking
    supplier_map = seed_suppliers()
    seed_purchases(supplier_map)

    # 3. Promotions
    seed_coupons()

    # 4. User Accounts & Reviews
    create_admin(app)
    create_customer(app)

    # 5. Operational Orders & POS Sales Transactions
    seed_orders_and_sales()

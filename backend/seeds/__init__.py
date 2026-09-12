"""
Seed orchestrator for e Grossary.
Loads all authentic FMCG categories, products, suppliers, purchases, coupons,
customer profiles, historical orders, and counter POS sales into the database.
"""


import os


def seed_all(app):
    """
    Orchestrate database seeding.
    In production and by default, only essential master catalog data (Categories,
    Products, Suppliers, Coupons, and Admin Account) are seeded if empty.
    Dummy operational transactions (fake orders, simulated sales, fake customer
    profiles, purchases, and fake reviews) are NEVER loaded unless explicitly
    requested via SEED_DUMMY_DATA=true.
    """
    from .categories import seed_categories
    from .products import seed_products
    from .suppliers import seed_suppliers
    from .coupons import seed_coupons
    from .users import create_admin

    # 1. Base Master Catalog
    cat_map = seed_categories()
    seed_products(cat_map)

    # 2. Master Suppliers
    supplier_map = seed_suppliers()

    # 3. Master Promotions & Vouchers
    seed_coupons()

    # 4. Essential Administrator Account
    create_admin(app)

    # 5. Ensure any dummy/legacy customer accounts are permanently purged
    from .users import create_customer
    create_customer(app)

    # 6. Simulated purchases/counter sales (Disabled by default for Production)
    if os.getenv('SEED_DUMMY_DATA', 'false').lower() == 'true':
        from .purchases import seed_purchases
        from .orders_and_sales import seed_orders_and_sales

        seed_purchases(supplier_map)
        seed_orders_and_sales()



"""
Authentic administrator, customer accounts, and product reviews seed data.
"""
from werkzeug.security import generate_password_hash
from database.models import db
from database.models.user import User
from database.models.product import Product, Review


def create_admin(app):
    """Create default admin user from config"""
    admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
    if not admin:
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            email=app.config.get('ADMIN_EMAIL', 'admin@mart.com'),
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            role='admin',
            full_name='Admin'
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Admin user created: {app.config['ADMIN_USERNAME']}")


def create_customer(app):
    """
    Ensure all dummy or legacy customer accounts are permanently purged.
    Customer accounts are created only through genuine customer registration.
    """
    dummy_usernames = ['customer', 'rahul_sharma', 'amit_choudhary', 'ramesh_bhai']
    dummy_emails = [
        'customer@mart.com',
        'rahul.sharma@gmail.com',
        'amit.choudhary@yahoo.com',
        'rameshbhai.patel@gmail.com'
    ]

    try:
        dummy_users = User.query.filter(
            (User.username.in_(dummy_usernames)) | (User.email.in_(dummy_emails))
        ).all()

        if dummy_users:
            dummy_ids = [u.id for u in dummy_users]
            Review.query.filter(Review.user_id.in_(dummy_ids)).delete(synchronize_session=False)
            for u in dummy_users:
                db.session.delete(u)
            db.session.commit()
            app.logger.info(f"Purged {len(dummy_users)} dummy customer account(s).")
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"Dummy customer purge deferred: {e}")


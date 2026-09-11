"""
Authentic promotional and discount coupons seed data for Jay Goga Mart.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from database.models import db
from database.models.promotion import Coupon


def seed_coupons():
    """Seed active promotional discounts and vouchers."""
    real_coupons = [
        {
            'code': 'WELCOME50',
            'discount_type': 'fixed',
            'value': Decimal('50.00'),
            'min_order_amount': Decimal('299.00'),
            'valid_until': datetime.now(timezone.utc) + timedelta(days=90),
            'usage_limit': 500,
            'times_used': 48,
            'is_active': True
        },
        {
            'code': 'JAYGOGA100',
            'discount_type': 'fixed',
            'value': Decimal('100.00'),
            'min_order_amount': Decimal('499.00'),
            'valid_until': datetime.now(timezone.utc) + timedelta(days=120),
            'usage_limit': 1000,
            'times_used': 135,
            'is_active': True
        },
        {
            'code': 'FRESH15',
            'discount_type': 'percentage',
            'value': Decimal('15.00'),
            'min_order_amount': Decimal('199.00'),
            'valid_until': datetime.now(timezone.utc) + timedelta(days=60),
            'usage_limit': 300,
            'times_used': 74,
            'is_active': True
        },
        {
            'code': 'GROCERY10',
            'discount_type': 'percentage',
            'value': Decimal('10.00'),
            'min_order_amount': Decimal('399.00'),
            'valid_until': datetime.now(timezone.utc) + timedelta(days=180),
            'usage_limit': 800,
            'times_used': 92,
            'is_active': True
        }
    ]

    for data in real_coupons:
        coupon = Coupon.query.filter_by(code=data['code']).first()
        if not coupon:
            coupon = Coupon(
                code=data['code'],
                discount_type=data['discount_type'],
                value=data['value'],
                min_order_amount=data['min_order_amount'],
                valid_until=data['valid_until'],
                usage_limit=data['usage_limit'],
                times_used=data['times_used'],
                is_active=data['is_active']
            )
            db.session.add(coupon)
    db.session.commit()

from datetime import datetime, timezone
from sqlalchemy import Numeric
from . import db

class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), default='percentage')
    value = db.Column(Numeric(10, 2), nullable=False)
    min_order_amount = db.Column(Numeric(10, 2), default=0)
    valid_until = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer, default=100)
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class Notification(db.Model):
    """Admin notification model for operational alerts"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    # user_id = None means it's a broadcast admin notification
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    # 'info', 'warning', 'danger', 'success'
    notif_type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False, index=True)
    link = db.Column(db.String(200))  # Optional deep-link into admin panel
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

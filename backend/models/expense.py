from datetime import datetime, timezone
from sqlalchemy import Numeric
from . import db

class Expense(db.Model):
    """Operating Expense model for store operational overhead tracking"""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # Rent, Electricity, Staff, Transport, Packaging, Maintenance, Other
    amount = db.Column(Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    payment_mode = db.Column(db.String(30), default='Cash')  # Cash, UPI, Bank Transfer, Cheque
    is_recurring = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    expense_type = db.Column(db.String(30), default='OpEx', index=True)  # OpEx, CapEx, Debt Recovery, Supplier Payment
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_by = db.Column(db.String(100), default='Admin')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': float(self.amount) if self.amount is not None else 0.0,
            'expense_date': self.expense_date.strftime('%Y-%m-%d') if self.expense_date else None,
            'payment_mode': self.payment_mode,
            'is_recurring': bool(getattr(self, 'is_recurring', False)),
            'description': self.description or '',
            'expense_type': self.expense_type or 'OpEx',
            'is_deleted': bool(self.is_deleted),
            'created_by': self.created_by or 'Admin',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }

    def __repr__(self):
        return f'<Expense #{self.id} {self.category} ({self.expense_type}) ₹{self.amount}>'

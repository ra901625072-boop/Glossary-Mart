from datetime import datetime, timezone
from sqlalchemy import Numeric
from . import db

class Supplier(db.Model):
    """Supplier model for tracking stock providers and Accounts Payable"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))
    bank_details = db.Column(db.String(200))
    outstanding_balance = db.Column(Numeric(10, 2), default=0.0)  # Accounts Payable liability
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    purchases = db.relationship('Purchase', backref='supplier', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person or '',
            'phone': self.phone or '',
            'email': self.email or '',
            'address': self.address or '',
            'gstin': self.gstin or '',
            'bank_details': self.bank_details or '',
            'outstanding_balance': float(self.outstanding_balance) if self.outstanding_balance is not None else 0.0,
            'purchases_count': len(self.purchases) if self.purchases else 0
        }

    def __repr__(self):
        return f'<Supplier {self.name} - AP ₹{self.outstanding_balance}>'


class Purchase(db.Model):
    """Purchase model for restocking inventory"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(Numeric(10, 2), nullable=False)
    total_cost = db.Column(Numeric(10, 2), nullable=False)
    invoice_number = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='Unpaid')  # Unpaid, Paid, Partial
    payment_mode = db.Column(db.String(30), default='Credit')    # Credit, Cash, Bank Transfer, Cheque
    purchase_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else 'Unknown',
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'quantity': self.quantity,
            'purchase_price': float(self.purchase_price) if self.purchase_price is not None else 0.0,
            'total_cost': float(self.total_cost) if self.total_cost is not None else 0.0,
            'invoice_number': self.invoice_number or f'INV-RESTOCK-{self.id}',
            'payment_status': self.payment_status or 'Unpaid',
            'payment_mode': self.payment_mode or 'Credit',
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d %H:%M:%S') if self.purchase_date else None
        }

    def __repr__(self):
        return f'<Purchase {self.id} - Product {self.product_id} - ₹{self.total_cost}>'

"""
Authentic FMCG and grocery distributors seed data for Jay Goga Mart.
"""
from database.models import db
from database.models.inventory import Supplier


def seed_suppliers():
    """Seed authentic regional FMCG and agri-commodity suppliers."""
    real_suppliers = [
        {
            'name': 'Gujarat Co-operative Milk Marketing Federation (Amul)',
            'contact_person': 'Ramesh Bhai Patel',
            'phone': '+91 2692 258506',
            'email': 'orders@amul.coop',
            'address': 'Amul Dairy Road, Anand, Gujarat 388001'
        },
        {
            'name': 'ITC Limited — Food & Staples Distribution',
            'contact_person': 'Vikram Mehta',
            'phone': '+91 79 2656 4300',
            'email': 'ahmedabad.sales@itc.in',
            'address': 'S.G. Highway, Bodakdev, Ahmedabad, Gujarat 380054'
        },
        {
            'name': 'Tata Consumer Products Regional Hub',
            'contact_person': 'Suresh Joshi',
            'phone': '+91 265 233 1140',
            'email': 'west.orders@tataconsumer.com',
            'address': 'GIDC Estate, Makarpura, Vadodara, Gujarat 390010'
        },
        {
            'name': 'Unjha APMC Spices & Commodity Mandi Traders',
            'contact_person': 'Rameshwar Lal Patel',
            'phone': '+91 2767 254210',
            'email': 'trade@unjhaspices.com',
            'address': 'APMC Market Yard, Station Road, Unjha, Mehsana, Gujarat 384170'
        },
        {
            'name': 'Hindustan Unilever Distribution Depot',
            'contact_person': 'Sanjay Rawat',
            'phone': '+91 2762 251120',
            'email': 'mehsana.supply@hul.com',
            'address': 'Radhanpur Road, Mehsana, Gujarat 384002'
        },
        {
            'name': 'Adani Wilmar Limited (Fortune Oils & Foods)',
            'contact_person': 'Dhaval Shah',
            'phone': '+91 79 2656 5555',
            'email': 'sales@adaniwilmar.in',
            'address': 'Fortune House, Navrangpura, Ahmedabad, Gujarat 380009'
        },
        {
            'name': 'Britannia Industries Sanand Logistics Hub',
            'contact_person': 'Ankit Verma',
            'phone': '+91 2717 618000',
            'email': 'orders.gujarat@britindia.com',
            'address': 'Sanand GIDC Phase II, Ahmedabad, Gujarat 382110'
        },
        {
            'name': 'Nestle India Western Distribution Centre',
            'contact_person': 'Pooja Nair',
            'phone': '+91 22 2497 0000',
            'email': 'consumer.care@in.nestle.com',
            'address': 'Sarkhej-Bawla Highway, Changodar, Ahmedabad, Gujarat 382213'
        }
    ]

    supplier_map = {}
    for data in real_suppliers:
        supplier = Supplier.query.filter_by(name=data['name']).first()
        if not supplier:
            supplier = Supplier(
                name=data['name'],
                contact_person=data['contact_person'],
                phone=data['phone'],
                email=data['email'],
                address=data['address']
            )
            db.session.add(supplier)
            db.session.flush()
        supplier_map[data['name']] = supplier.id
    db.session.commit()
    return supplier_map

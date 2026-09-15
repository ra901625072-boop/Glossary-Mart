"""Admin Point-of-Sale routes (POS interface + checkout API)."""
from datetime import datetime, timezone
from flask import current_app, jsonify, request
from sqlalchemy import func

from backend.models import db
from backend.models.product import Product, Sale, PosBill
from backend.models.user import User
from backend.services.inventory_service import InventoryService
from backend.routes.decorators import admin_required
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/pos')
@admin_required
def pos():
    """POS (Point of Sale) — returns JSON product list for POS UI."""
    pos_products = (
        db.session.query(Product)
        .filter(Product.stock_quantity > 0, Product.is_active == True)  # noqa: E712
        .order_by(Product.name)
        .all()
    )
    return jsonify({
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'selling_price': float(p.selling_price),
                'cost_price': float(p.cost_price),
                'stock_quantity': p.stock_quantity,
                'category': p.category_rel.name if p.category_rel else 'General',
                'hsn_code': p.hsn_code or '1904',
                'gst_rate': float(p.gst_rate) if p.gst_rate is not None else 5.0,
                'image_path': p.image_path or '',
            }
            for p in pos_products
        ]
    })


@admin_bp.route('/api/pos/checkout', methods=['POST'])
@admin_bp.route('/pos/checkout', methods=['POST'])
@admin_required
def pos_checkout():
    """
    Enterprise POS checkout JSON API.
    Creates an immutable PosBill invoice header, assigns sequential bill number,
    deducts stock atomically, pro-rates counter discounts, and records dual GST.
    """
    data = request.get_json(silent=True) or {}
    cart_items = data.get('cart') or data.get('items') or []

    if not cart_items:
        return jsonify({'success': False, 'error': 'Cart is empty.'}), 400

    customer_phone = (data.get('customer_phone') or data.get('phone') or '').strip()
    customer_name = (data.get('customer_name') or data.get('name') or 'Walk-in').strip()
    payment_mode = (data.get('payment_mode') or data.get('payment_method') or 'Cash').strip()
    try:
        discount_amount = max(0.0, float(data.get('discount_amount') or data.get('discount') or 0.0))
    except (ValueError, TypeError):
        discount_amount = 0.0

    now = datetime.now(timezone.utc)

    # First pass: validate items and compute raw subtotal
    validated_items = []
    subtotal_raw = 0.0

    try:
        for item in cart_items:
            try:
                product_id = int(item.get('id') or item.get('product_id'))
                qty = int(item.get('qty') or item.get('quantity', 0))
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Invalid product ID or quantity.'}), 400

            if qty <= 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Quantity must be greater than zero.'}), 400

            product = db.session.get(Product, product_id)
            if not product:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Product #{product_id} not found.'}), 404

            if product.stock_quantity < qty:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Insufficient stock for "{product.name}". Available: {product.stock_quantity}.',
                }), 400

            item_line_total = float(product.selling_price) * qty
            subtotal_raw += item_line_total
            validated_items.append({
                'product': product,
                'qty': qty,
                'line_total': item_line_total,
                'unit_price': float(product.selling_price),
                'unit_cost': float(product.cost_price),
            })

        if subtotal_raw <= 0:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Total bill amount must be greater than zero.'}), 400

        actual_discount = round(min(discount_amount, subtotal_raw), 2)
        net_total = round(subtotal_raw - actual_discount, 2)
        # Standard retail tax calculation (5% GST included)
        tax_amount = round(net_total * 0.05 / 1.05, 2)

        # Detect Udhar (Store Credit / Khata Book) payment mode
        is_udhar = any(k in payment_mode.lower() for k in ('udhar', 'credit', 'khata'))
        customer_user = None

        if is_udhar:
            clean_digits = ''.join(filter(str.isdigit, customer_phone))
            has_name = bool(customer_name and customer_name not in ('Walk-in', 'Walk-in Counter'))
            if not clean_digits and not has_name:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': 'Customer mobile number or name is required for Udhar (Store Credit / Khata) billing.'
                }), 400

            # 1. Look up existing customer in database
            if customer_phone:
                customer_user = db.session.query(User).filter(
                    User.phone == customer_phone,
                    User.role == 'customer'
                ).first()
            if not customer_user and has_name:
                customer_user = db.session.query(User).filter(
                    (User.full_name.ilike(customer_name) | (User.username.ilike(customer_name))),
                    User.role == 'customer'
                ).first()

            # 2. Provision new customer profile if first-time in-store Khata customer
            if not customer_user:
                cust_key = clean_digits or f"instore_{int(now.timestamp())}"
                uname = f"khata_{cust_key}"
                # Ensure unique username
                existing_uname = db.session.query(User).filter_by(username=uname).first()
                if existing_uname:
                    uname = f"khata_{cust_key}_{int(now.timestamp()) % 10000}"
                email_val = f"{cust_key}@khata.egrossary.com"
                display_name = customer_name if has_name else f"Customer {customer_phone}"

                customer_user = User(
                    username=uname,
                    email=email_val,
                    full_name=display_name,
                    phone=customer_phone,
                    role='customer',
                    credit=0.0,
                    is_verified=True,
                )
                customer_user.set_password("InStoreKhata@123")
                db.session.add(customer_user)
                db.session.flush()

            # 3. Increase customer unpaid credit balance (Accounts Receivable debt)
            customer_user.credit = float(customer_user.credit or 0.0) + net_total
            customer_name = customer_user.full_name or customer_name
            customer_phone = customer_user.phone or customer_phone
            payment_mode = 'Udhar'

        # Generate statutory consecutive sequential bill serial (e.g. EG/26/POS-00001)
        max_id = db.session.query(func.coalesce(func.max(PosBill.id), 0)).scalar() or 0
        next_seq = max_id + 1
        bill_number = f"EG/{now.strftime('%y')}/POS-{next_seq:05d}"

        pos_bill = PosBill(
            bill_number=bill_number,
            customer_name=customer_name or 'Walk-in',
            customer_phone=customer_phone or '',
            subtotal=subtotal_raw,
            discount_amount=actual_discount,
            tax_amount=tax_amount,
            total_amount=net_total,
            payment_method=payment_mode,
            cashier_name='Administrator',
            created_at=now,
        )
        db.session.add(pos_bill)
        db.session.flush()

        # Second pass: deduct stock and create linked Sale rows with pro-rated discount
        for item in validated_items:
            product = item['product']
            qty = item['qty']
            line_total = item['line_total']

            # Pro-rate counter discount to individual items
            item_discount = round(actual_discount * (line_total / subtotal_raw), 2) if subtotal_raw > 0 else 0.0
            item_net_revenue = max(0.0, round(line_total - item_discount, 2))
            item_gross_profit = (item['unit_price'] - item['unit_cost']) * qty
            item_net_profit = max(0.0, round(item_gross_profit - item_discount, 2))

            ok, msg = InventoryService.deduct_stock(product.id, qty, triggered_by='pos')
            if not ok:
                db.session.rollback()
                return jsonify({'success': False, 'error': msg}), 400

            sale = Sale(
                product_id=product.id,
                bill_id=pos_bill.id,
                quantity=qty,
                total_price=item_net_revenue,
                profit=item_net_profit,
                sale_date=now,
            )
            db.session.add(sale)

        db.session.commit()

        if is_udhar and customer_user:
            _log_action(
                'POS_UDHAR_SALE', 'User', customer_user.id,
                details=f"Billed invoice {bill_number} for ₹{net_total:.2f} to Udhar account for {customer_user.full_name or customer_user.username} (Phone: {customer_user.phone or 'N/A'}). Total Udhar balance: ₹{float(customer_user.credit):.2f}"
            )
        else:
            _log_action(
                'POS_COUNTER_SALE', 'PosBill', pos_bill.id,
                details=f"Issued invoice {bill_number} for ₹{net_total:.2f} ({payment_mode}) to {customer_phone or customer_name}"
            )

        return jsonify({
            'success': True,
            'bill_id': pos_bill.id,
            'bill_number': pos_bill.bill_number,
            'total': net_total,
            'subtotal': subtotal_raw,
            'discount': actual_discount,
            'tax': tax_amount,
            'cgst': round(tax_amount / 2, 2),
            'sgst': round(tax_amount / 2, 2),
            'payment_mode': payment_mode,
            'customer_phone': customer_phone or 'Walk-in',
            'customer_name': customer_name or 'Walk-in',
            'is_udhar': is_udhar,
            'customer_credit': float(customer_user.credit) if customer_user else 0.0,
            'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        })

    except Exception:
        db.session.rollback()
        current_app.logger.exception("POS checkout failed")
        return jsonify({'success': False, 'error': 'A server error occurred during checkout. Please try again.'}), 500


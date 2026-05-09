import csv
import hashlib
import io
from datetime import datetime, timedelta, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from sqlalchemy import func

from app.models import Order, Product, Sale, db

def hash_token(token):
    """Securely hash a token using SHA-256"""
    if not token:
        return None
    return hashlib.sha256(token.encode()).hexdigest()


def get_sales_stats(days=1):
    """
    Get combined sales and profit statistics (Manual Sales + Online Orders)
    """
    from decimal import Decimal
    from app.models import OrderItem
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # 1. Manual Sales Stats
    sale_stats = db.session.query(
        func.coalesce(func.sum(Sale.total_price), 0).label('total_sales'),
        func.coalesce(func.sum(Sale.profit), 0).label('total_profit'),
        func.count(Sale.id).label('transaction_count')
    ).filter(Sale.sale_date >= start_date).first()
    
    # 2. Online Orders Stats
    order_stats = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0).label('total_sales'),
        func.count(Order.id).label('transaction_count')
    ).filter(Order.created_at >= start_date, Order.order_status != 'Cancelled').first()
    
    order_profit = db.session.query(
        func.coalesce(func.sum(OrderItem.profit), 0)
    ).join(Order).filter(Order.created_at >= start_date, Order.order_status != 'Cancelled').scalar() or 0
    
    total_sales = Decimal(str(sale_stats.total_sales)) + Decimal(str(order_stats.total_sales))
    total_profit = Decimal(str(sale_stats.total_profit)) + Decimal(str(order_profit))
    transaction_count = int(sale_stats.transaction_count or 0) + int(order_stats.transaction_count or 0)
    
    return {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'transaction_count': transaction_count,
        'period': f'Last {days} day{"s" if days > 1 else ""}'
    }


def get_monthly_comparison():
    """
    Compare current month vs last month (Combined Manual + Online)
    """
    now = datetime.now(timezone.utc)
    from decimal import Decimal
    from app.models import OrderItem
    
    current_month_start = datetime(now.year, now.month, 1)
    if now.month == 1:
        last_month_start = datetime(now.year - 1, 12, 1)
        last_month_end = datetime(now.year, 1, 1)
    else:
        last_month_start = datetime(now.year, now.month - 1, 1)
        last_month_end = current_month_start
    
    def get_combined_stats(start, end=None):
        sale_q = db.session.query(func.sum(Sale.total_price), func.sum(Sale.profit)).filter(Sale.sale_date >= start)
        order_q = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= start, Order.order_status != 'Cancelled')
        profit_q = db.session.query(func.sum(OrderItem.profit)).join(Order).filter(Order.created_at >= start, Order.order_status != 'Cancelled')
        
        if end:
            sale_q = sale_q.filter(Sale.sale_date < end)
            order_q = order_q.filter(Order.created_at < end)
            profit_q = profit_q.filter(Order.created_at < end)
            
        s_res = sale_q.first()
        o_res = order_q.first()
        p_res = profit_q.scalar() or 0
        
        total_s = Decimal(str(s_res[0] or 0)) + Decimal(str(o_res[0] or 0))
        total_p = Decimal(str(s_res[1] or 0)) + Decimal(str(p_res))
        return total_s, total_p

    curr_s, curr_p = get_combined_stats(current_month_start)
    last_s, last_p = get_combined_stats(last_month_start, last_month_end)
    
    sales_change = ((curr_s - last_s) / last_s * Decimal('100')) if last_s > 0 else Decimal('0')
    profit_change = ((curr_p - last_p) / last_p * Decimal('100')) if last_p > 0 else Decimal('0')
    
    return {
        'current_month': {'sales': curr_s, 'profit': curr_p, 'name': now.strftime('%B %Y')},
        'last_month': {'sales': last_s, 'profit': last_p, 'name': last_month_start.strftime('%B %Y')},
        'changes': {'sales_change': round(sales_change, 2), 'profit_change': round(profit_change, 2)}
    }


def get_yearly_comparison():
    """
    Compare current year vs last year (Combined Manual + Online)
    """
    now = datetime.now(timezone.utc)
    from decimal import Decimal
    from app.models import OrderItem
    
    current_year_start = datetime(now.year, 1, 1)
    last_year_start = datetime(now.year - 1, 1, 1)
    last_year_end = datetime(now.year, 1, 1)
    
    def get_combined_stats(start, end=None):
        sale_q = db.session.query(func.sum(Sale.total_price), func.sum(Sale.profit)).filter(Sale.sale_date >= start)
        order_q = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= start, Order.order_status != 'Cancelled')
        profit_q = db.session.query(func.sum(OrderItem.profit)).join(Order).filter(Order.created_at >= start, Order.order_status != 'Cancelled')
        
        if end:
            sale_q = sale_q.filter(Sale.sale_date < end)
            order_q = order_q.filter(Order.created_at < end)
            profit_q = profit_q.filter(Order.created_at < end)
            
        s_res = sale_q.first()
        o_res = order_q.first()
        p_res = profit_q.scalar() or 0
        
        total_s = Decimal(str(s_res[0] or 0)) + Decimal(str(o_res[0] or 0))
        total_p = Decimal(str(s_res[1] or 0)) + Decimal(str(p_res))
        return total_s, total_p

    curr_s, curr_p = get_combined_stats(current_year_start)
    last_s, last_p = get_combined_stats(last_year_start, last_year_end)
    
    sales_change = ((curr_s - last_s) / last_s * Decimal('100')) if last_s > 0 else Decimal('0')
    profit_change = ((curr_p - last_p) / last_p * Decimal('100')) if last_p > 0 else Decimal('0')
    
    return {
        'current_year': {'sales': curr_s, 'profit': curr_p, 'year': now.year},
        'last_year': {'sales': last_s, 'profit': last_p, 'year': now.year - 1},
        'changes': {'sales_change': round(sales_change, 2), 'profit_change': round(profit_change, 2)}
    }


def get_chart_data(days=30):
    """
    Get daily sales and profit data for charts (combining Manual Sales and Customer Orders)
    
    Args:
        days (int): Number of days to include in chart
        
    Returns:
        dict: Dictionary with labels and data arrays for Chart.js
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    end_date = datetime.now(timezone.utc) + timedelta(days=1)  # Include today fully
    
    # 1. Get Manual Sales Data
    manual_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.sum(Sale.total_price).label('sales'),
        func.sum(Sale.profit).label('profit')
    ).filter(
        Sale.sale_date >= start_date
    ).group_by(
        func.date(Sale.sale_date)
    ).all()
    
    # 2. Get Customer Orders Data (excluding Cancelled)
    customer_orders = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total_amount).label('sales'),
        # We need to join with OrderItem to get profit, or calculate it differently.
        # Since Order doesn't have a profit column in the DB (it's a property), 
        # we can't sum it directly in SQL easily without a join or complex query.
        # HOWEVER, the user wants a graph.
        # Let's iterate and sum in python for simplicity and correctness if dataset is small,
        # OR better: Add a join.
    ).filter(
        Order.created_at >= start_date,
        Order.order_status != 'Cancelled'
    ).group_by(
        func.date(Order.created_at)
    ).all()
    
    # We need profit for orders. Since 'total_profit' is a property, we can't group by it easily in SQL.
    # Let's fetch all orders in the range and aggregate in Python.
    # This is safer to avoid complex SQL with properties.
    
    all_orders = Order.query.filter(
        Order.created_at >= start_date,
        Order.order_status != 'Cancelled'
    ).all()
    
    from decimal import Decimal
    order_data = {}
    for order in all_orders:
        date_str = order.created_at.strftime('%Y-%m-%d')
        if date_str not in order_data:
            order_data[date_str] = {'sales': Decimal('0'), 'profit': Decimal('0')}
        order_data[date_str]['sales'] += Decimal(str(order.total_amount))
        order_data[date_str]['profit'] += Decimal(str(order.total_profit))

    # Process Manual Sales into Dictionary
    sales_data_dict = {}
    for record in manual_sales:
        # SQLite returns string for date in group_by usually
        date_str = record.date if isinstance(record.date, str) else record.date.strftime('%Y-%m-%d')
        if date_str not in sales_data_dict:
            sales_data_dict[date_str] = {'sales': Decimal('0'), 'profit': Decimal('0')}
        sales_data_dict[date_str]['sales'] += Decimal(str(record.sales or 0))
        sales_data_dict[date_str]['profit'] += Decimal(str(record.profit or 0))
        
    # Merge Data
    final_data = {}
    
    # Create range of dates
    for i in range(days):
        current_date = (datetime.now(timezone.utc) - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
        final_data[current_date] = {'sales': Decimal('0'), 'profit': Decimal('0')}
        
    # Fill with Manual Sales
    for date_str, stats in sales_data_dict.items():
        if date_str in final_data:
            final_data[date_str]['sales'] += stats['sales']
            final_data[date_str]['profit'] += stats['profit']
            
    # Fill with Customer Orders
    for date_str, stats in order_data.items():
        if date_str in final_data:
            final_data[date_str]['sales'] += stats['sales']
            final_data[date_str]['profit'] += stats['profit']
    
    # Convert to Lists for Chart.js (Charts need floats or strings usually)
    labels = sorted(final_data.keys())
    sales_list = [float(final_data[d]['sales']) for d in labels]
    profit_list = [float(final_data[d]['profit']) for d in labels]
    
    return {
        'labels': labels,
        'sales': sales_list,
        'profit': profit_list
    }


def get_stock_stats():
    """
    Get stock statistics for charts
    
    Returns:
        dict: Labels and data for stock charts
    """
    # 1. Stock Value by Category
    products = Product.query.all()
    
    category_stock = {}
    
    for product in products:
        cat_name = product.category_rel.name if product.category_rel else (product.category or 'Uncategorized')
        stock_value = product.stock_quantity * product.cost_price
        
        if cat_name not in category_stock:
            category_stock[cat_name] = 0
        category_stock[cat_name] += stock_value
        
    # 2. Top 5 Products by Stock Quantity
    top_stock_products = sorted(products, key=lambda x: x.stock_quantity, reverse=True)[:5]
    top_stock_labels = [p.name for p in top_stock_products]
    top_stock_values = [p.stock_quantity for p in top_stock_products]

    # 3. Low Stock Products (Quantity < minimum_stock_alert)
    low_stock_products = [
        {'name': p.name, 'stock': p.stock_quantity, 'id': p.id, 'min_stock': p.minimum_stock_alert} 
        for p in products if p.stock_quantity <= p.minimum_stock_alert
    ]
    low_stock_products = sorted(low_stock_products, key=lambda x: x['stock'])

    return {
        'category_labels': list(category_stock.keys()),
        'category_values': list(category_stock.values()),
        'top_products_labels': top_stock_labels,
        'top_products_values': top_stock_values,
        'low_stock_products': low_stock_products
    }


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_sales_csv(sales):
    """Generate CSV from sales records"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Product', 'Category', 'Quantity', 'Price', 'Profit', 'Date'])
    
    for sale in sales:
        writer.writerow([
            f"#SAL-{sale.id:04d}",
            sale.product.name if sale.product else 'Deleted Product',
            (sale.product.category_rel.name if sale.product and sale.product.category_rel else sale.product.category) if sale.product else 'N/A',
            sale.quantity,
            f"INR {sale.total_price:.2f}",
            f"INR {sale.profit:.2f}",
            sale.sale_date.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return output.getvalue()


def generate_sales_pdf(sales, start_date=None, end_date=None):
    """Generate PDF from sales records using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1A237E'), # ss-primary
        spaceAfter=12,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=30,
        alignment=1
    )
    
    # Header content
    elements.append(Paragraph("Jay Goga Kirana Store", title_style))
    
    date_range = "Full History"
    if start_date and end_date:
        date_range = f"Sales Report: {start_date} to {end_date}"
    elements.append(Paragraph(date_range, subtitle_style))
    
    # Table data
    data = [['ID', 'Product', 'Category', 'Qty', 'Price (INR)', 'Profit (INR)', 'Timestamp']]
    
    total_revenue = 0
    total_profit = 0
    
    for sale in sales:
        total_revenue += sale.total_price
        total_profit += sale.profit
        
        data.append([
            f"#SAL-{sale.id:04d}",
            sale.product.name if sale.product else 'Deleted',
            (sale.product.category_rel.name if sale.product and sale.product.category_rel else sale.product.category) if sale.product else 'N/A',
            str(sale.quantity),
            f"{sale.total_price:,.2f}",
            f"{sale.profit:,.2f}",
            sale.sale_date.strftime('%Y-%m-%d %H:%M')
        ])
    
    # Summary Row
    data.append(['', '', 'TOTAL', '', f"{total_revenue:,.2f}", f"{total_profit:,.2f}", ''])
    
    # Table styling
    t = Table(data, colWidths=[0.8*inch, 2.5*inch, 1.5*inch, 0.6*inch, 1.2*inch, 1.2*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A237E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1A237E')),
    ]))
    
    elements.append(t)
    
    # Build PDF
    doc.build(elements)
    
    return buffer.getvalue()

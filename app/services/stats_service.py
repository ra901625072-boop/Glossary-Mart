from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func
from app.models import db, Order, OrderItem, Product, Sale

def get_sales_stats(days=1):
    """Get combined sales and profit statistics (Manual Sales + Online Orders)"""
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
    """Compare current month vs last month (Combined Manual + Online)"""
    now = datetime.now(timezone.utc)
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
    """Compare current year vs last year (Combined Manual + Online)"""
    now = datetime.now(timezone.utc)
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
    """Get daily sales and profit data for Chart.js"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    manual_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.sum(Sale.total_price).label('sales'),
        func.sum(Sale.profit).label('profit')
    ).filter(Sale.sale_date >= start_date).group_by(func.date(Sale.sale_date)).all()
    
    all_orders = Order.query.filter(Order.created_at >= start_date, Order.order_status != 'Cancelled').all()
    
    order_data = {}
    for order in all_orders:
        date_str = order.created_at.strftime('%Y-%m-%d')
        if date_str not in order_data:
            order_data[date_str] = {'sales': Decimal('0'), 'profit': Decimal('0')}
        order_data[date_str]['sales'] += Decimal(str(order.total_amount))
        order_data[date_str]['profit'] += Decimal(str(order.total_profit))

    sales_data_dict = {}
    for record in manual_sales:
        date_str = record.date if isinstance(record.date, str) else record.date.strftime('%Y-%m-%d')
        if date_str not in sales_data_dict:
            sales_data_dict[date_str] = {'sales': Decimal('0'), 'profit': Decimal('0')}
        sales_data_dict[date_str]['sales'] += Decimal(str(record.sales or 0))
        sales_data_dict[date_str]['profit'] += Decimal(str(record.profit or 0))
        
    final_data = {}
    for i in range(days):
        current_date = (datetime.now(timezone.utc) - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
        final_data[current_date] = {'sales': Decimal('0'), 'profit': Decimal('0')}
        
    for date_str, stats in sales_data_dict.items():
        if date_str in final_data:
            final_data[date_str]['sales'] += stats['sales']
            final_data[date_str]['profit'] += stats['profit']
            
    for date_str, stats in order_data.items():
        if date_str in final_data:
            final_data[date_str]['sales'] += stats['sales']
            final_data[date_str]['profit'] += stats['profit']
    
    labels = sorted(final_data.keys())
    return {
        'labels': labels,
        'sales': [float(final_data[d]['sales']) for d in labels],
        'profit': [float(final_data[d]['profit']) for d in labels]
    }

def get_stock_stats():
    """Get stock statistics for charts"""
    products = Product.query.all()
    category_stock = {}
    
    for product in products:
        cat_name = product.category_rel.name if product.category_rel else (product.category or 'Uncategorized')
        stock_value = product.stock_quantity * product.cost_price
        category_stock[cat_name] = category_stock.get(cat_name, 0) + stock_value
        
    top_stock_products = sorted(products, key=lambda x: x.stock_quantity, reverse=True)[:5]
    low_stock_products = sorted([
        {'name': p.name, 'stock': p.stock_quantity, 'id': p.id, 'min_stock': p.minimum_stock_alert} 
        for p in products if p.stock_quantity <= p.minimum_stock_alert
    ], key=lambda x: x['stock'])

    return {
        'category_labels': list(category_stock.keys()),
        'category_values': [float(v) for v in category_stock.values()],
        'top_products_labels': [p.name for p in top_stock_products],
        'top_products_values': [p.stock_quantity for p in top_stock_products],
        'low_stock_products': low_stock_products
    }

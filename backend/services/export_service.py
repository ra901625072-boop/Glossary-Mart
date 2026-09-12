import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

def sanitize_csv_cell(val):
    """
    Sanitizes values to prevent CSV Formula Injection (CWE-1236).
    If a cell begins with '=', '+', '-', '@', tab, or carriage return,
    prefix with a single quote to neutralize formula execution.
    """
    if val is None:
        return ''
    s = str(val)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{s}"
    return s


def generate_sales_csv(sales):
    """Generate CSV from sales records with formula injection protection."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Product', 'Category', 'Quantity', 'Price', 'Profit', 'Date'])
    
    for sale in sales:
        product_name = sale.product.name if sale.product else 'Deleted Product'
        category_name = (sale.product.category_rel.name if sale.product and sale.product.category_rel else sale.product.category) if sale.product else 'N/A'
        writer.writerow([
            sanitize_csv_cell(f"#SAL-{sale.id:04d}"),
            sanitize_csv_cell(product_name),
            sanitize_csv_cell(category_name),
            sale.quantity,
            sanitize_csv_cell(f"INR {sale.total_price:.2f}"),
            sanitize_csv_cell(f"INR {sale.profit:.2f}"),
            sale.sale_date.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return output.getvalue()

def generate_sales_pdf(sales, start_date=None, end_date=None):
    """Generate PDF from sales records using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1A237E'), spaceAfter=12, alignment=1)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=12, textColor=colors.grey, spaceAfter=30, alignment=1)
    
    elements.append(Paragraph("e Grossary Store", title_style))
    date_range = f"Sales Report: {start_date} to {end_date}" if start_date and end_date else "Full History"
    elements.append(Paragraph(date_range, subtitle_style))
    
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
    
    data.append(['', '', 'TOTAL', '', f"{total_revenue:,.2f}", f"{total_profit:,.2f}", ''])
    
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
    doc.build(elements)
    return buffer.getvalue()


def generate_order_invoice_pdf(order):
    """Generate invoice PDF for a customer order using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0f766e'), spaceAfter=4, alignment=0)
    normal_style = ParagraphStyle('Norm', parent=styles['Normal'], fontSize=9, textColor=colors.black, spaceAfter=3)
    
    elements.append(Paragraph("<b>e Grossary Superstore</b>", title_style))
    elements.append(Paragraph(f"Tax Invoice &bull; Order #{order.id}", styles['Heading2']))
    elements.append(Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %b %Y, %I:%M %p') if order.created_at else 'N/A'}", normal_style))
    cust_name = order.user.full_name or order.user.username if order.user else 'Valued Customer'
    elements.append(Paragraph(f"<b>Customer:</b> {cust_name}", normal_style))
    elements.append(Paragraph(f"<b>Shipping Address:</b> {order.shipping_address or 'Store Pickup'}", normal_style))
    elements.append(Paragraph(f"<b>Payment Method:</b> {order.payment_method} ({order.payment_status})", normal_style))
    elements.append(Paragraph("<br/>", normal_style))
    
    data = [['#', 'Item Description', 'Qty', 'Unit Price', 'Subtotal']]
    for idx, item in enumerate(order.order_items, 1):
        pname = item.product.name if item.product else 'Grocery Item'
        data.append([str(idx), pname, str(item.quantity), f"INR {float(item.price):.2f}", f"INR {float(item.subtotal):.2f}"])
    
    data.append(['', '', '', 'GRAND TOTAL:', f"INR {float(order.total_amount):.2f}"])
    
    t = Table(data, colWidths=[0.5*inch, 3.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t)
    doc.build(elements)
    return buffer.getvalue()


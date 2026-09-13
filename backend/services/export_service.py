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
    """Generate professional GST Tax Invoice PDF for an e-grocery order using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#065f46'),
        spaceAfter=2,
        alignment=0,
    )
    sub_title_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#475569'),
        spaceAfter=6,
    )
    section_head = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=8,
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        'Norm',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=2,
    )

    # 1. Header: Seller & Store Details
    elements.append(Paragraph("<b>eGrossary Superstore</b>", title_style))
    elements.append(Paragraph("eGrossary Retail Pvt. Ltd. &bull; APMC Market Hub, Sector 19, Vashi, Navi Mumbai, MH 400705", sub_title_style))
    elements.append(Paragraph("<b>GSTIN:</b> 27AABCE1234F1Z5 &bull; <b>FSSAI Lic:</b> 11521034000123", sub_title_style))
    elements.append(Paragraph("<hr color='#cbd5e1' width='100%'/>", normal_style))

    # 2. Tax Invoice Meta Info
    invoice_date = order.created_at.strftime('%d %b %Y, %I:%M %p') if getattr(order, 'created_at', None) else 'N/A'
    user_obj = getattr(order, 'user', None)
    cust_name = (user_obj.full_name or user_obj.username) if user_obj else 'Valued Customer'
    cust_email = getattr(user_obj, 'email', '') or 'N/A'
    cust_phone = getattr(user_obj, 'phone', '') or 'N/A'
    shipping_addr = getattr(order, 'shipping_address', None) or 'Customer Doorstep'

    meta_data = [
        [
            Paragraph(f"<b>Invoice No:</b> INV-EGM-{order.id:05d}<br/><b>Invoice Date:</b> {invoice_date}<br/><b>Order Ref:</b> #EGM-{order.id}", normal_style),
            Paragraph(f"<b>Billed & Shipped To:</b><br/><b>{cust_name}</b><br/>{shipping_addr}<br/>Email: {cust_email} | Phone: {cust_phone}", normal_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[3.5 * inch, 3.5 * inch])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)

    elements.append(Paragraph(f"<b>Payment:</b> {order.payment_status} ({order.payment_method}) &bull; <b>Delivery Mode:</b> 15-Minute Express", normal_style))
    elements.append(Paragraph("<br/>", normal_style))

    # 3. Itemized Grocery Table
    table_data = [['#', 'Grocery Item Description', 'Qty', 'Unit Price', 'Subtotal']]
    items = getattr(order, 'order_items', []) or []
    subtotal_sum = 0.0

    for idx, item in enumerate(items, 1):
        pname = item.product.name if getattr(item, 'product', None) else 'Grocery Item'
        qty = item.quantity or 1
        u_price = float(item.price or 0.0)
        item_sub = float(item.subtotal if hasattr(item, 'subtotal') else (u_price * qty))
        subtotal_sum += item_sub
        table_data.append([
            str(idx),
            pname,
            str(qty),
            f"INR {u_price:.2f}",
            f"INR {item_sub:.2f}",
        ])

    order_total = float(order.total_amount if order.total_amount is not None else subtotal_sum)
    taxable_val = order_total / 1.05
    cgst_val = (order_total - taxable_val) / 2.0
    sgst_val = cgst_val

    # Summary rows
    table_data.append(['', '', '', 'Taxable Value:', f"INR {taxable_val:.2f}"])
    table_data.append(['', '', '', 'CGST (2.5%):', f"INR {cgst_val:.2f}"])
    table_data.append(['', '', '', 'SGST (2.5%):', f"INR {sgst_val:.2f}"])
    table_data.append(['', '', '', 'GRAND TOTAL:', f"INR {order_total:.2f}"])

    item_table = Table(table_data, colWidths=[0.4 * inch, 3.6 * inch, 0.7 * inch, 1.1 * inch, 1.2 * inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#065f46')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -5), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 1), (-1, -5), colors.whitesmoke),
        ('BACKGROUND', (0, -4), (-1, -1), colors.HexColor('#f8fafc')),
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, -1), (-1, -1), 10),
        ('TEXTCOLOR', (2, -1), (-1, -1), colors.HexColor('#065f46')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#065f46')),
    ]))
    elements.append(item_table)

    # 4. Footer Declaration
    elements.append(Paragraph("<br/>", normal_style))
    decl_style = ParagraphStyle(
        'DeclStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#64748b'),
        leading=10,
    )
    elements.append(Paragraph("<b>Declaration:</b> This is a computer-generated tax invoice and does not require a physical signature. All fresh groceries are 100% inspected and quality assured. For any questions, contact support@egrossary.com.", decl_style))

    doc.build(elements)
    return buffer.getvalue()



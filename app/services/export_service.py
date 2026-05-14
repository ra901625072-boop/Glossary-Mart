import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

def generate_sales_csv(sales):
    """Generate CSV from sales records"""
    output = io.StringIO()
    writer = csv.writer(output)
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
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1A237E'), spaceAfter=12, alignment=1)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=12, textColor=colors.grey, spaceAfter=30, alignment=1)
    
    elements.append(Paragraph("Jay Goga Kirana Store", title_style))
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

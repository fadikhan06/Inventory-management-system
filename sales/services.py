"""
Sales service layer: invoice number generation, PDF invoice, stock deduction.
"""
import io
from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas

from inventory.models import InventoryMovement, Notification


def generate_invoice_number(shop_id: int) -> str:
    """Generate a unique invoice number: INV-{shop_id}-{YYYYMMDD}-{seq}."""
    from sales.models import Sale
    today = timezone.now().date()
    prefix = f"INV-{shop_id}-{today.strftime('%Y%m%d')}"
    count = Sale.objects.filter(invoice_number__startswith=prefix).count()
    return f"{prefix}-{count + 1:04d}"


def complete_sale(sale, items_data: list, performed_by) -> None:
    """
    Deduct stock for each sold item and record inventory movements.

    items_data: list of dicts with keys: product, quantity, unit_price, unit_cost
    """
    from sales.models import SaleItem
    for item_data in items_data:
        product = item_data['product']
        quantity = item_data['quantity']
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=item_data['unit_price'],
            unit_cost=item_data['unit_cost'],
        )
        # Deduct stock
        product.stock_qty = max(0, product.stock_qty - quantity)
        product.save(update_fields=['stock_qty'])
        # Record movement
        InventoryMovement.objects.create(
            product=product,
            movement_type=InventoryMovement.MOVEMENT_OUT,
            quantity=-quantity,
            notes=f'Sale {sale.invoice_number}',
            performed_by=performed_by,
        )
        # Low-stock notification
        if product.is_low_stock:
            exists = Notification.objects.filter(
                shop=sale.shop,
                product=product,
                notification_type=Notification.TYPE_LOW_STOCK,
                is_read=False,
            ).exists()
            if not exists:
                Notification.objects.create(
                    shop=sale.shop,
                    notification_type=Notification.TYPE_LOW_STOCK,
                    title=f'Low stock: {product.name}',
                    message=(
                        f'"{product.name}" has only {product.stock_qty} units remaining '
                        f'(threshold: {product.low_stock_threshold}).'
                    ),
                    product=product,
                )


def generate_invoice_pdf(sale) -> bytes:
    """Generate a PDF invoice for a Sale and return bytes."""
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont('Helvetica-Bold', 18)
    c.drawString(2 * cm, height - 2 * cm, 'INVOICE')
    c.setFont('Helvetica', 10)
    c.drawString(2 * cm, height - 3 * cm, f'Invoice #: {sale.invoice_number}')
    c.drawString(2 * cm, height - 3.6 * cm, f'Date: {sale.created_at.strftime("%Y-%m-%d %H:%M")}')
    c.drawString(2 * cm, height - 4.2 * cm, f'Shop: {sale.shop.name}')
    c.drawString(2 * cm, height - 4.8 * cm, f'Customer: {sale.customer_name or "Walk-in"}')
    c.drawString(2 * cm, height - 5.4 * cm, f'Cashier: {sale.cashier.get_full_name() or sale.cashier.username}')

    # Table header
    y = height - 7 * cm
    c.setFont('Helvetica-Bold', 10)
    c.drawString(2 * cm, y, 'Product')
    c.drawString(10 * cm, y, 'Qty')
    c.drawString(13 * cm, y, 'Unit Price')
    c.drawString(17 * cm, y, 'Total')
    c.line(2 * cm, y - 0.3 * cm, 19 * cm, y - 0.3 * cm)

    # Items
    y -= 0.8 * cm
    c.setFont('Helvetica', 10)
    for item in sale.items.select_related('product'):
        c.drawString(2 * cm, y, item.product.name[:35])
        c.drawString(10 * cm, y, str(item.quantity))
        c.drawString(13 * cm, y, f'{item.unit_price:.2f}')
        c.drawString(17 * cm, y, f'{item.line_total:.2f}')
        y -= 0.6 * cm
        if y < 5 * cm:
            c.showPage()
            y = height - 2 * cm

    # Totals
    c.line(2 * cm, y - 0.2 * cm, 19 * cm, y - 0.2 * cm)
    y -= 0.8 * cm
    c.setFont('Helvetica-Bold', 10)
    c.drawString(14 * cm, y, f'Subtotal: {sale.subtotal:.2f}')
    y -= 0.6 * cm
    c.drawString(14 * cm, y, f'Discount: {sale.discount:.2f}')
    y -= 0.6 * cm
    c.drawString(14 * cm, y, f'TOTAL: {sale.total:.2f}')
    y -= 1 * cm
    c.setFont('Helvetica', 9)
    c.drawString(2 * cm, y, 'Thank you for your purchase!')

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

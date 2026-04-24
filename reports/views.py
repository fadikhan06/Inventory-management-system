"""
Reports views: daily/weekly/monthly sales, profit, CSV/PDF export.
"""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.utils import timezone

from sales.models import Sale, SaleItem
from inventory.models import Product
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas


def get_shop(request):
    try:
        return request.user.profile.shop
    except Exception:
        return None


def _build_report(shop, start_date, end_date):
    """Build a report dict for the given date range."""
    sales = Sale.objects.filter(
        shop=shop,
        status=Sale.STATUS_COMPLETED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).prefetch_related('items').select_related('cashier')

    total_revenue = sum(s.total for s in sales)
    total_profit = sum(s.total_profit for s in sales)
    total_discount = sum(s.discount for s in sales)
    total_transactions = sales.count()

    # Top products
    items = SaleItem.objects.filter(
        sale__shop=shop,
        sale__status=Sale.STATUS_COMPLETED,
        sale__created_at__date__gte=start_date,
        sale__created_at__date__lte=end_date,
    ).select_related('product')

    product_totals = {}
    for item in items:
        pid = item.product_id
        if pid not in product_totals:
            product_totals[pid] = {
                'name': item.product.name,
                'qty': 0,
                'revenue': Decimal('0'),
                'profit': Decimal('0'),
            }
        product_totals[pid]['qty'] += item.quantity
        product_totals[pid]['revenue'] += item.line_total
        product_totals[pid]['profit'] += item.line_profit

    top_products = sorted(product_totals.values(), key=lambda x: x['revenue'], reverse=True)[:10]

    return {
        'start_date': start_date,
        'end_date': end_date,
        'sales': sales,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_discount': total_discount,
        'total_transactions': total_transactions,
        'top_products': top_products,
    }


class ReportView(LoginRequiredMixin, View):
    """Main report view with date-range and period filters."""

    template_name = 'reports/report.html'

    def get(self, request):
        shop = get_shop(request)
        today = timezone.now().date()

        period = request.GET.get('period', 'today')
        if period == 'today':
            start, end = today, today
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            end = today
        elif period == 'month':
            start = today.replace(day=1)
            end = today
        elif period == 'custom':
            try:
                start = date.fromisoformat(request.GET.get('start', str(today)))
                end = date.fromisoformat(request.GET.get('end', str(today)))
            except ValueError:
                start, end = today, today
        else:
            start, end = today, today

        report = _build_report(shop, start, end) if shop else {}

        period_choices = [
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
        ]

        return render(request, self.template_name, {
            'report': report,
            'period': period,
            'start': start,
            'end': end,
            'period_choices': period_choices,
        })


class ReportCSVView(LoginRequiredMixin, View):
    """Export sales report as CSV."""

    def get(self, request):
        shop = get_shop(request)
        today = timezone.now().date()
        period = request.GET.get('period', 'today')
        if period == 'today':
            start, end = today, today
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            end = today
        elif period == 'month':
            start = today.replace(day=1)
            end = today
        elif period == 'custom':
            try:
                start = date.fromisoformat(request.GET.get('start', str(today)))
                end = date.fromisoformat(request.GET.get('end', str(today)))
            except ValueError:
                start, end = today, today
        else:
            start, end = today, today

        report = _build_report(shop, start, end) if shop else {}
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="report_{start}_{end}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice #', 'Date', 'Customer', 'Cashier', 'Subtotal', 'Discount', 'Total', 'Profit'])
        for s in report.get('sales', []):
            writer.writerow([
                s.invoice_number,
                s.created_at.strftime('%Y-%m-%d %H:%M'),
                s.customer_name or 'Walk-in',
                s.cashier.username if s.cashier else '',
                s.subtotal,
                s.discount,
                s.total,
                s.total_profit,
            ])
        writer.writerow([])
        writer.writerow(['', '', '', 'Total Revenue:', report.get('total_revenue', 0)])
        writer.writerow(['', '', '', 'Total Profit:', report.get('total_profit', 0)])
        return response


class ReportPDFView(LoginRequiredMixin, View):
    """Export sales report as PDF."""

    def get(self, request):
        shop = get_shop(request)
        today = timezone.now().date()
        period = request.GET.get('period', 'today')
        if period == 'today':
            start, end = today, today
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            end = today
        elif period == 'month':
            start = today.replace(day=1)
            end = today
        elif period == 'custom':
            try:
                start = date.fromisoformat(request.GET.get('start', str(today)))
                end = date.fromisoformat(request.GET.get('end', str(today)))
            except ValueError:
                start, end = today, today
        else:
            start, end = today, today

        report = _build_report(shop, start, end) if shop else {}

        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        c.setFont('Helvetica-Bold', 16)
        c.drawString(2 * cm, height - 2 * cm, 'Sales Report')
        c.setFont('Helvetica', 10)
        c.drawString(2 * cm, height - 2.8 * cm, f'Period: {start} to {end}')
        if shop:
            c.drawString(2 * cm, height - 3.4 * cm, f'Shop: {shop.name}')

        y = height - 5 * cm
        c.setFont('Helvetica-Bold', 10)
        c.drawString(2 * cm, y, f'Total Transactions: {report.get("total_transactions", 0)}')
        y -= 0.6 * cm
        c.drawString(2 * cm, y, f'Total Revenue: {report.get("total_revenue", 0):.2f}')
        y -= 0.6 * cm
        c.drawString(2 * cm, y, f'Total Profit: {report.get("total_profit", 0):.2f}')
        y -= 0.6 * cm
        c.drawString(2 * cm, y, f'Total Discount: {report.get("total_discount", 0):.2f}')

        y -= 1.2 * cm
        c.setFont('Helvetica-Bold', 10)
        c.drawString(2 * cm, y, 'Invoice #')
        c.drawString(7 * cm, y, 'Date')
        c.drawString(12 * cm, y, 'Total')
        c.drawString(15 * cm, y, 'Profit')
        c.line(2 * cm, y - 0.3 * cm, 19 * cm, y - 0.3 * cm)
        y -= 0.8 * cm

        c.setFont('Helvetica', 9)
        for s in report.get('sales', []):
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm
            c.drawString(2 * cm, y, s.invoice_number[:20])
            c.drawString(7 * cm, y, s.created_at.strftime('%Y-%m-%d'))
            c.drawString(12 * cm, y, f'{s.total:.2f}')
            c.drawString(15 * cm, y, f'{s.total_profit:.2f}')
            y -= 0.5 * cm

        c.save()
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{start}_{end}.pdf"'
        return response

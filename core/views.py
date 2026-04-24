"""
Core views: Dashboard and Notification management.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from inventory.models import Product, Notification, Shop
from sales.models import Sale, SaleItem


def get_shop(request):
    """Return the shop associated with the logged-in user's profile, or None."""
    try:
        return request.user.profile.shop
    except Exception:
        return None


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with key metrics."""

    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        shop = get_shop(self.request)

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        products_qs = Product.objects.filter(shop=shop, is_active=True) if shop else Product.objects.none()
        sales_qs = Sale.objects.filter(shop=shop, status=Sale.STATUS_COMPLETED) if shop else Sale.objects.none()

        # Today's sales
        today_sales = sales_qs.filter(created_at__date=today)
        today_revenue = sum(s.total for s in today_sales)
        today_profit = sum(s.total_profit for s in today_sales)

        # Weekly
        week_sales = sales_qs.filter(created_at__date__gte=week_start)
        week_revenue = sum(s.total for s in week_sales)

        # Monthly
        month_sales = sales_qs.filter(created_at__date__gte=month_start)
        month_revenue = sum(s.total for s in month_sales)

        # Stock value
        stock_value = sum(p.cost_price * p.stock_qty for p in products_qs)

        # Low stock products
        low_stock = [p for p in products_qs if p.is_low_stock]

        # Recent sales (last 10)
        recent_sales = sales_qs.select_related('cashier')[:10]

        # Notifications
        notifications = Notification.objects.filter(shop=shop, is_read=False)[:5] if shop else []

        ctx.update({
            'total_products': products_qs.count(),
            'total_stock_units': products_qs.aggregate(total=Sum('stock_qty'))['total'] or 0,
            'low_stock_count': len(low_stock),
            'low_stock_products': low_stock[:10],
            'today_sales_count': today_sales.count(),
            'today_revenue': today_revenue,
            'today_profit': today_profit,
            'week_revenue': week_revenue,
            'month_revenue': month_revenue,
            'stock_value': stock_value,
            'recent_sales': recent_sales,
            'notifications': notifications,
        })
        return ctx


class NotificationsView(LoginRequiredMixin, ListView):
    """List all notifications for the current shop."""

    template_name = 'core/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        shop = get_shop(self.request)
        if not shop:
            return Notification.objects.none()
        return Notification.objects.filter(shop=shop).order_by('-created_at')


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark a single notification as read."""

    def post(self, request, pk):
        shop = get_shop(request)
        notif = get_object_or_404(Notification, pk=pk, shop=shop)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return JsonResponse({'status': 'ok'})


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read for the current shop."""

    def post(self, request):
        shop = get_shop(request)
        if shop:
            Notification.objects.filter(shop=shop, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('core:notifications')

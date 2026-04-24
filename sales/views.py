"""
Sales views: POS entry, invoice display, PDF export, sales history.
"""
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models import Q

from inventory.models import Product, Category
from .models import Sale, SaleItem
from .forms import SaleForm
from .services import generate_invoice_number, complete_sale, generate_invoice_pdf


def get_shop(request):
    try:
        return request.user.profile.shop
    except Exception:
        return None


class SaleCreateView(LoginRequiredMixin, View):
    """POS/sales entry view."""
    template_name = 'sales/sale_create.html'

    def get(self, request):
        shop = get_shop(request)
        form = SaleForm()
        products = Product.objects.filter(shop=shop, is_active=True, stock_qty__gt=0).select_related('category') if shop else []
        categories = Category.objects.filter(shop=shop) if shop else []
        return render(request, self.template_name, {
            'form': form, 'products': products, 'categories': categories
        })

    def post(self, request):
        shop = get_shop(request)
        form = SaleForm(request.POST)
        # Parse cart from JSON body
        try:
            cart = json.loads(request.POST.get('cart_data', '[]'))
        except (json.JSONDecodeError, TypeError):
            cart = []

        if not cart:
            messages.error(request, 'Cart is empty. Please add items before completing the sale.')
            products = Product.objects.filter(shop=shop, is_active=True, stock_qty__gt=0).select_related('category') if shop else []
            categories = Category.objects.filter(shop=shop) if shop else []
            return render(request, self.template_name, {'form': form, 'products': products, 'categories': categories})

        if form.is_valid():
            sale = form.save(commit=False)
            sale.shop = shop
            sale.cashier = request.user
            sale.invoice_number = generate_invoice_number(shop.pk)
            sale.save()

            items_data = []
            errors = []
            for entry in cart:
                try:
                    product = Product.objects.get(pk=entry['product_id'], shop=shop, is_active=True)
                    qty = int(entry['quantity'])
                    if qty <= 0:
                        continue
                    if product.stock_qty < qty:
                        errors.append(f'Insufficient stock for "{product.name}" (available: {product.stock_qty}).')
                        continue
                    items_data.append({
                        'product': product,
                        'quantity': qty,
                        'unit_price': product.selling_price,
                        'unit_cost': product.cost_price,
                    })
                except (Product.DoesNotExist, KeyError, ValueError):
                    errors.append(f'Invalid product entry: {entry}')

            if errors:
                sale.delete()
                for err in errors:
                    messages.error(request, err)
                products = Product.objects.filter(shop=shop, is_active=True, stock_qty__gt=0).select_related('category') if shop else []
                categories = Category.objects.filter(shop=shop) if shop else []
                return render(request, self.template_name, {'form': form, 'products': products, 'categories': categories})

            complete_sale(sale, items_data, request.user)
            messages.success(request, f'Sale completed! Invoice: {sale.invoice_number}')
            return redirect('sales:sale_detail', pk=sale.pk)

        products = Product.objects.filter(shop=shop, is_active=True, stock_qty__gt=0).select_related('category') if shop else []
        categories = Category.objects.filter(shop=shop) if shop else []
        return render(request, self.template_name, {'form': form, 'products': products, 'categories': categories})


class SaleListView(LoginRequiredMixin, ListView):
    """Sales history list."""
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 25

    def get_queryset(self):
        shop = get_shop(self.request)
        qs = Sale.objects.filter(shop=shop).select_related('cashier').prefetch_related('items') if shop else Sale.objects.none()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer_name__icontains=q))
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_status'] = self.request.GET.get('status', '')
        return ctx


class SaleDetailView(LoginRequiredMixin, DetailView):
    """Invoice detail / receipt view."""
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

    def get_queryset(self):
        shop = get_shop(self.request)
        return Sale.objects.filter(shop=shop).prefetch_related('items__product').select_related('cashier', 'shop') if shop else Sale.objects.none()


class SaleInvoicePDFView(LoginRequiredMixin, View):
    """Download invoice as PDF."""

    def get(self, request, pk):
        shop = get_shop(request)
        sale = get_object_or_404(Sale, pk=pk, shop=shop)
        pdf_bytes = generate_invoice_pdf(sale)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{sale.invoice_number}.pdf"'
        return response


class SaleVoidView(LoginRequiredMixin, View):
    """Void a sale (admin only)."""

    def post(self, request, pk):
        from accounts.models import UserProfile
        try:
            if request.user.profile.role != UserProfile.ROLE_ADMIN:
                messages.error(request, 'Admin access required.')
                return redirect('sales:sale_list')
        except Exception:
            messages.error(request, 'Admin access required.')
            return redirect('sales:sale_list')

        shop = get_shop(request)
        sale = get_object_or_404(Sale, pk=pk, shop=shop, status=Sale.STATUS_COMPLETED)
        sale.status = Sale.STATUS_VOIDED
        sale.save(update_fields=['status'])
        # Restore stock
        for item in sale.items.select_related('product'):
            item.product.stock_qty += item.quantity
            item.product.save(update_fields=['stock_qty'])
        messages.success(request, f'Sale {sale.invoice_number} voided and stock restored.')
        return redirect('sales:sale_detail', pk=sale.pk)

"""
Inventory views: Product and Category CRUD, barcode search, stock adjustment,
shop management, and low-stock notifications.
"""
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models import Q

from .models import Product, Category, Shop, InventoryMovement, Notification
from .forms import ProductForm, CategoryForm, ShopForm, StockAdjustmentForm
from accounts.models import UserProfile


def get_shop(request):
    try:
        return request.user.profile.shop
    except Exception:
        return None


def is_admin(request):
    try:
        return request.user.profile.role == UserProfile.ROLE_ADMIN
    except Exception:
        return False


# ─────────────────────────── SHOP ───────────────────────────

class ShopListView(LoginRequiredMixin, ListView):
    model = Shop
    template_name = 'inventory/shop_list.html'
    context_object_name = 'shops'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class ShopCreateView(LoginRequiredMixin, View):
    template_name = 'inventory/shop_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': ShopForm(), 'action': 'Create'})

    def post(self, request):
        form = ShopForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop created.')
            return redirect('inventory:shop_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class ShopEditView(LoginRequiredMixin, View):
    template_name = 'inventory/shop_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        return render(request, self.template_name, {'form': ShopForm(instance=shop), 'action': 'Edit'})

    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop updated.')
            return redirect('inventory:shop_list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit'})


# ─────────────────────────── CATEGORY ───────────────────────────

class CategoryListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        shop = get_shop(self.request)
        return Category.objects.filter(shop=shop).order_by('name') if shop else Category.objects.none()


class CategoryCreateView(LoginRequiredMixin, View):
    template_name = 'inventory/category_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': CategoryForm(), 'action': 'Create'})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.shop = get_shop(request)
            category.save()
            messages.success(request, 'Category created.')
            return redirect('inventory:category_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class CategoryEditView(LoginRequiredMixin, View):
    template_name = 'inventory/category_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        shop = get_shop(request)
        category = get_object_or_404(Category, pk=pk, shop=shop)
        return render(request, self.template_name, {'form': CategoryForm(instance=category), 'action': 'Edit'})

    def post(self, request, pk):
        shop = get_shop(request)
        category = get_object_or_404(Category, pk=pk, shop=shop)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('inventory:category_list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit'})


class CategoryDeleteView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        shop = get_shop(request)
        category = get_object_or_404(Category, pk=pk, shop=shop)
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('inventory:category_list')


# ─────────────────────────── PRODUCT ───────────────────────────

class ProductListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 25

    def get_queryset(self):
        shop = get_shop(self.request)
        qs = Product.objects.filter(shop=shop, is_active=True).select_related('category') if shop else Product.objects.none()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))
        cat = self.request.GET.get('category', '')
        if cat:
            qs = qs.filter(category_id=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        shop = get_shop(self.request)
        ctx['categories'] = Category.objects.filter(shop=shop) if shop else []
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_cat'] = self.request.GET.get('category', '')
        return ctx


class ProductDetailView(LoginRequiredMixin, DetailView):
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        shop = get_shop(self.request)
        return Product.objects.filter(shop=shop).select_related('category') if shop else Product.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['movements'] = self.object.movements.select_related('performed_by')[:20]
        return ctx


class ProductCreateView(LoginRequiredMixin, View):
    template_name = 'inventory/product_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        shop = get_shop(request)
        form = ProductForm(shop=shop)
        return render(request, self.template_name, {'form': form, 'action': 'Create'})

    def post(self, request):
        shop = get_shop(request)
        form = ProductForm(request.POST, shop=shop)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = shop
            product.save()
            # Record initial stock movement
            if product.stock_qty > 0:
                InventoryMovement.objects.create(
                    product=product,
                    movement_type=InventoryMovement.MOVEMENT_IN,
                    quantity=product.stock_qty,
                    notes='Initial stock',
                    performed_by=request.user,
                )
            # Check low stock immediately
            _check_low_stock(product, shop)
            messages.success(request, f'Product "{product.name}" created.')
            return redirect('inventory:product_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class ProductEditView(LoginRequiredMixin, View):
    template_name = 'inventory/product_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        shop = get_shop(request)
        product = get_object_or_404(Product, pk=pk, shop=shop)
        form = ProductForm(instance=product, shop=shop)
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'product': product})

    def post(self, request, pk):
        shop = get_shop(request)
        product = get_object_or_404(Product, pk=pk, shop=shop)
        old_qty = product.stock_qty
        form = ProductForm(request.POST, instance=product, shop=shop)
        if form.is_valid():
            product = form.save()
            new_qty = product.stock_qty
            if new_qty != old_qty:
                diff = new_qty - old_qty
                InventoryMovement.objects.create(
                    product=product,
                    movement_type=InventoryMovement.MOVEMENT_ADJUSTMENT,
                    quantity=diff,
                    notes='Manual edit',
                    performed_by=request.user,
                )
            _check_low_stock(product, shop)
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect('inventory:product_list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'product': product})


class ProductDeleteView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        shop = get_shop(request)
        product = get_object_or_404(Product, pk=pk, shop=shop)
        product.is_active = False
        product.save(update_fields=['is_active'])
        messages.success(request, f'Product "{product.name}" deactivated.')
        return redirect('inventory:product_list')


class ProductBarcodeSearchView(LoginRequiredMixin, View):
    """JSON endpoint for barcode/POS lookup (used by sales POS)."""

    def get(self, request):
        barcode = request.GET.get('barcode', '').strip()
        shop = get_shop(request)
        if not barcode or not shop:
            return JsonResponse({'found': False})
        try:
            product = Product.objects.get(
                Q(barcode=barcode) | Q(sku=barcode),
                shop=shop,
                is_active=True
            )
            return JsonResponse({
                'found': True,
                'id': product.pk,
                'name': product.name,
                'sku': product.sku,
                'barcode': product.barcode,
                'selling_price': str(product.selling_price),
                'stock_qty': product.stock_qty,
            })
        except Product.DoesNotExist:
            return JsonResponse({'found': False})
        except Product.MultipleObjectsReturned:
            product = Product.objects.filter(
                Q(barcode=barcode) | Q(sku=barcode), shop=shop, is_active=True
            ).first()
            return JsonResponse({
                'found': True,
                'id': product.pk,
                'name': product.name,
                'sku': product.sku,
                'barcode': product.barcode,
                'selling_price': str(product.selling_price),
                'stock_qty': product.stock_qty,
            })


class StockAdjustView(LoginRequiredMixin, View):
    """Manual stock adjustment."""

    template_name = 'inventory/stock_adjust.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        shop = get_shop(request)
        product = get_object_or_404(Product, pk=pk, shop=shop)
        form = StockAdjustmentForm()
        return render(request, self.template_name, {'form': form, 'product': product})

    def post(self, request, pk):
        shop = get_shop(request)
        product = get_object_or_404(Product, pk=pk, shop=shop)
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            notes = form.cleaned_data.get('notes', '')
            product.stock_qty = max(0, product.stock_qty + qty)
            product.save(update_fields=['stock_qty'])
            InventoryMovement.objects.create(
                product=product,
                movement_type=InventoryMovement.MOVEMENT_ADJUSTMENT,
                quantity=qty,
                notes=notes or 'Manual stock adjustment',
                performed_by=request.user,
            )
            _check_low_stock(product, shop)
            messages.success(request, f'Stock adjusted by {qty:+d}. New qty: {product.stock_qty}.')
            return redirect('inventory:product_detail', pk=product.pk)
        return render(request, self.template_name, {'form': form, 'product': product})


class ProductExportCSVView(LoginRequiredMixin, View):
    """Export all products as CSV."""

    def get(self, request):
        shop = get_shop(request)
        products = Product.objects.filter(shop=shop, is_active=True).select_related('category') if shop else []

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'SKU', 'Barcode', 'Category', 'Cost Price',
                         'Selling Price', 'Stock Qty', 'Low Stock Threshold'])
        for p in products:
            writer.writerow([
                p.name, p.sku, p.barcode,
                p.category.name if p.category else '',
                p.cost_price, p.selling_price, p.stock_qty, p.low_stock_threshold
            ])
        return response


# ─────────────────────────── HELPERS ───────────────────────────

def _check_low_stock(product, shop):
    """Create a low-stock notification if the product is at/below threshold."""
    if product.is_low_stock:
        # Avoid duplicate unread notifications for same product
        existing = Notification.objects.filter(
            shop=shop,
            product=product,
            notification_type=Notification.TYPE_LOW_STOCK,
            is_read=False,
        ).exists()
        if not existing:
            Notification.objects.create(
                shop=shop,
                notification_type=Notification.TYPE_LOW_STOCK,
                title=f'Low stock: {product.name}',
                message=(
                    f'"{product.name}" has only {product.stock_qty} units remaining '
                    f'(threshold: {product.low_stock_threshold}).'
                ),
                product=product,
            )

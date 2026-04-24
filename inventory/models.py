"""
Inventory models: Shop, Category, Product, InventoryMovement, Notification.
"""
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Shop(models.Model):
    """Represents a physical or logical shop/store."""

    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Product category."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ('name', 'shop')

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product with stock tracking, pricing, and barcode support."""

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_qty = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=getattr(settings, 'LOW_STOCK_DEFAULT', 10)
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        """True when stock is at or below the low stock threshold."""
        return self.stock_qty <= self.low_stock_threshold

    @property
    def profit_margin(self):
        """Profit per unit sold."""
        return self.selling_price - self.cost_price


class InventoryMovement(models.Model):
    """Audit trail for every stock change."""

    MOVEMENT_IN = 'in'
    MOVEMENT_OUT = 'out'
    MOVEMENT_ADJUSTMENT = 'adjustment'
    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, 'Stock In'),
        (MOVEMENT_OUT, 'Stock Out (Sale)'),
        (MOVEMENT_ADJUSTMENT, 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.IntegerField()  # positive = in, negative = out
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name}: {self.movement_type} {self.quantity}"


class Notification(models.Model):
    """System notifications (e.g., low-stock alerts)."""

    TYPE_LOW_STOCK = 'low_stock'
    TYPE_INFO = 'info'
    TYPE_WARNING = 'warning'
    TYPE_CHOICES = [
        (TYPE_LOW_STOCK, 'Low Stock Alert'),
        (TYPE_INFO, 'Information'),
        (TYPE_WARNING, 'Warning'),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    title = models.CharField(max_length=200)
    message = models.TextField()
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

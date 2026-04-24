"""
Sales models: Sale, SaleItem.
"""
from django.db import models
from django.contrib.auth.models import User
from inventory.models import Product, Shop


class Sale(models.Model):
    """A sales transaction."""

    STATUS_COMPLETED = 'completed'
    STATUS_VOIDED = 'voided'
    STATUS_CHOICES = [
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_VOIDED, 'Voided'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales')
    cashier = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='sales'
    )
    customer_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

    @property
    def subtotal(self):
        """Sum of all sale item totals before discount."""
        return sum(item.line_total for item in self.items.all())

    @property
    def total(self):
        """Grand total after discount."""
        return self.subtotal - self.discount

    @property
    def total_profit(self):
        """Profit = sum of (selling_price - cost_price) * quantity for each item."""
        return sum(item.line_profit for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class SaleItem(models.Model):
    """A line item within a sale."""

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot at sale time
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)   # snapshot at sale time

    class Meta:
        unique_together = ('sale', 'product')

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def line_profit(self):
        """Profit for this line: (selling_price - cost_price) * quantity."""
        return (self.unit_price - self.unit_cost) * self.quantity

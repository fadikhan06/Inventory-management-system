"""Forms for inventory management: products, categories, shops."""
from django import forms
from .models import Product, Category, Shop


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'address', 'phone', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'description', 'category',
            'cost_price', 'selling_price', 'stock_qty', 'low_stock_threshold', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or type barcode'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_qty': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop:
            self.fields['category'].queryset = Category.objects.filter(shop=shop)

    def clean(self):
        cleaned_data = super().clean()
        cost = cleaned_data.get('cost_price', 0)
        selling = cleaned_data.get('selling_price', 0)
        if selling is not None and cost is not None and selling < cost:
            self.add_error('selling_price', 'Selling price must be ≥ cost price.')
        return cleaned_data


class StockAdjustmentForm(forms.Form):
    """Form to manually adjust stock quantity."""
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Use positive values to add stock, negative to remove.'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )

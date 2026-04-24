"""Forms for the sales module."""
from django import forms
from .models import Sale


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer_name', 'discount', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name (optional)'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'value': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        }

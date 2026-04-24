"""Inventory URL configuration."""
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Shops
    path('shops/', views.ShopListView.as_view(), name='shop_list'),
    path('shops/create/', views.ShopCreateView.as_view(), name='shop_create'),
    path('shops/<int:pk>/edit/', views.ShopEditView.as_view(), name='shop_edit'),
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    # Products
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<int:pk>/adjust/', views.StockAdjustView.as_view(), name='stock_adjust'),
    path('products/export/csv/', views.ProductExportCSVView.as_view(), name='product_export_csv'),
    # API
    path('api/barcode/', views.ProductBarcodeSearchView.as_view(), name='barcode_search'),
]

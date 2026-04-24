"""Sales URL configuration."""
from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.SaleCreateView.as_view(), name='sale_create'),
    path('history/', views.SaleListView.as_view(), name='sale_list'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('<int:pk>/pdf/', views.SaleInvoicePDFView.as_view(), name='sale_pdf'),
    path('<int:pk>/void/', views.SaleVoidView.as_view(), name='sale_void'),
]

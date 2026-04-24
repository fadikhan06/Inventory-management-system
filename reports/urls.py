"""Reports URL configuration."""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportView.as_view(), name='report'),
    path('csv/', views.ReportCSVView.as_view(), name='report_csv'),
    path('pdf/', views.ReportPDFView.as_view(), name='report_pdf'),
]

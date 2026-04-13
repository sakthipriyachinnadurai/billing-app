""" API routes under project root """
from django.urls import path
from products.views import BillDetailView, CustomerPurchaseListView, GenerateBillView

urlpatterns = [
    path("generate-bill/", GenerateBillView.as_view(), name="generate_bill"),
    path("bills/customer/<str:email>/", CustomerPurchaseListView.as_view()),
    path("bills/<str:invoice_id>/", BillDetailView.as_view()),
]

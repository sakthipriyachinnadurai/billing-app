""" Register models on Admin Portal """

from django.contrib import admin
from .models import BillHistory, Product

admin.site.site_header = "Billing System Admin"
admin.site.site_title = "Billing System Admin Portal"
admin.site.index_title = "Welcome to the Billing System Admin Portal"

admin.site.register(Product)
admin.site.register(BillHistory)

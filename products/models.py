from django.db import models

class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"<Product product_id={self.product_id!r} name={self.name!r}>"

class BillHistory(models.Model):
    invoice_id = models.CharField(max_length=100, unique=True)
    customer_email = models.EmailField()
    products_list = models.JSONField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_id
    
    def __repr__(self):
        return f"<BillHistory invoice_id={self.invoice_id!r}>"

    class Meta:
        ordering = ["-transaction_time"]
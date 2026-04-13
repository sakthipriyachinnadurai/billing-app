""" Load or refresh default stationery products """

from products.models import Product
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Seed or refresh small stationery products."

    def handle(self, *args, **kwargs):
        seed_products()
        self.stdout.write(self.style.SUCCESS("Products seeded / updated."))


def seed_products():
    products = [
        {
            "product_id": "PROD001",
            "name": "Ball pen (blue)",
            "description": "Single ballpoint pen",
            "price": 10.00,
            "stock": 500,
            "tax_rate": 5,
        },
        {
            "product_id": "PROD002",
            "name": "Pencil HB",
            "description": "Single wood pencil",
            "price": 5.00,
            "stock": 600,
            "tax_rate": 5,
        },
        {
            "product_id": "PROD003",
            "name": "Eraser",
            "description": "Soft rubber eraser",
            "price": 8.00,
            "stock": 400,
            "tax_rate": 5,
        },
        {
            "product_id": "PROD004",
            "name": "Ruler 15cm",
            "description": "Plastic ruler",
            "price": 15.00,
            "stock": 300,
            "tax_rate": 5,
        },
        {
            "product_id": "PROD005",
            "name": "Notebook A5",
            "description": "40 pages ruled",
            "price": 45.00,
            "stock": 200,
            "tax_rate": 5,
        },
        {
            "product_id": "PROD006",
            "name": "Sharpener",
            "description": "Metal blade sharpener",
            "price": 12.00,
            "stock": 350,
            "tax_rate": 5,
        },
    ]
    # Create or Update products
    for p in products:
        pid = p["product_id"]
        Product.objects.update_or_create(
            product_id=pid,
            defaults={
                "name": p["name"],
                "description": p["description"],
                "price": p["price"],
                "stock": p["stock"],
                "tax_rate": p["tax_rate"],
            },
        )

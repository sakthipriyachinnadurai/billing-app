"""
Request validation for POST /generate-bill/.

Validates:
- customer email (mandatory)
- product items
- stock availability
- accepted cash denominations
- total amount with tax
- payment sufficiency
- whether exact change can be returned

"""
from decimal import Decimal
from .models import Product
from django.conf import settings
from rest_framework import serializers
from .utils import get_change_breakdown


class ProductItemSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000)

    def validate_product_id(self, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise serializers.ValidationError("Product ID is required.")
        return cleaned


class BillSerializer(serializers.Serializer):
    customer_email = serializers.EmailField()
    products_list = ProductItemSerializer(many=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2,  min_value=Decimal("1.00"))
    denominations = serializers.DictField(
        child=serializers.IntegerField(min_value=0)
    )

    def validate_products_list(self, value):
        # Ensure at least one product is added
        if not value:
            raise serializers.ValidationError("Add at least one product to the bill.")

        product_ids = []
        seen = set()
        
        # Prevent duplicate product IDs in same bill.
        for item in value:
            pid = item["product_id"]
            if pid in seen:
                raise serializers.ValidationError(f"Duplicate product: {pid}")
            seen.add(pid)
            product_ids.append(pid)

        # Fetch all requested products
        products = Product.objects.filter(product_id__in=product_ids)
        product_map = {product.product_id: product for product in products}

        # Ensure every requested product exists
        missing = [pid for pid in product_ids if pid not in product_map]
        if missing:
            raise serializers.ValidationError(
                f"Product not found: {', '.join(missing)}"
            )

        # Validate stock availability
        for item in value:
            product = product_map[item["product_id"]]
            if item["quantity"] > product.stock:
                raise serializers.ValidationError(
                    f"Insufficient stock for {product.product_id}"
                )

        self.product_map = product_map
        return value

    def validate_denominations(self, value):            
        accepted = set(settings.ACCEPTED_DENOMINATIONS)
        # Allow only accepted denominations in the payload
        for note_key in value:
            try:
                note_int = int(note_key)
            except (TypeError, ValueError):
                raise serializers.ValidationError(f"Invalid note: {note_key}")

            if note_int not in accepted:
                raise serializers.ValidationError(f"Invalid note: {note_key}")

        normalized = {}
        
        # Fill missing notes with 0
        for note_int in settings.ACCEPTED_DENOMINATIONS:
            key = str(note_int)
            normalized[key] = value.get(key, 0)

        return normalized

    def validate(self, data):
        # Normalize email
        data["customer_email"] = (
            data["customer_email"].strip().lower()
        )
        
        total = Decimal("0.00")
        #  Calculate bill total including tax
        for item in data["products_list"]:
            product = self.product_map[item["product_id"]]
            quantity = item["quantity"]

            line_total = product.price * quantity
            tax_amount = (line_total * product.tax_rate) / Decimal("100")
            total += line_total + tax_amount

        data["total_amount"] = total
        paid = data["amount_paid"]

        # Ensure payment covers total amount
        if paid < total:
            raise serializers.ValidationError({
                "error": "Insufficient payment",
                "required": str(total),
                "received": str(paid),
            })

        balance = paid - total
        data["balance_amount"] = balance

        # If change required, verify drawer can return exact amount
        if balance > 0:
            try:
                get_change_breakdown(balance, data["denominations"])
            except ValueError as exc:
                raise serializers.ValidationError({
                    "denominations": str(exc)
                }) from exc

        return data

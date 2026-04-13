"""
Tests for billing API:
- success flow
- serializer / API validations
- history endpoints
- bill detail endpoint
"""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import BillHistory, Product


class BillingAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(
            product_id="PROD001",
            name="Ball Pen",
            description="Blue pen",
            price=Decimal("10.00"),
            stock=50,
            tax_rate=Decimal("5.00"),
        )
        Product.objects.create(
            product_id="PROD002",
            name="Notebook",
            description="A5 notebook",
            price=Decimal("40.00"),
            stock=20,
            tax_rate=Decimal("5.00"),
        )

    def get_valid_payload(self):
        return {
            "customer_email": "test@example.com",
            "products_list": [
                {"product_id": "PROD001", "quantity": 2},
                {"product_id": "PROD002", "quantity": 1},
            ],
            "amount_paid": "100.00",
            "denominations": {
                "50": 2,
                "20": 2,
                "10": 5,
                "5": 5,
                "2": 10,
                "1": 10,
                "500": 1,
            },
        }

    def test_generate_bill_success(self):
        response = self.client.post(
            "/generate-bill/",
            self.get_valid_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BillHistory.objects.count(), 1)

        bill = BillHistory.objects.first()
        self.assertEqual(
            bill.customer_email,
            "test@example.com",
        )

    def test_customer_email_required(self):
        payload = self.get_valid_payload()
        payload["customer_email"] = ""

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("customer_email", response.data)

    def test_invalid_email(self):
        payload = self.get_valid_payload()
        payload["customer_email"] = "wrong-email"

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_empty_products_list(self):
        payload = self.get_valid_payload()
        payload["products_list"] = []

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_duplicate_product(self):
        payload = self.get_valid_payload()
        payload["products_list"] = [
            {"product_id": "PROD001", "quantity": 1},
            {"product_id": "PROD001", "quantity": 2},
        ]

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_product_not_found(self):
        payload = self.get_valid_payload()
        payload["products_list"][0]["product_id"] = "INVALID"

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_insufficient_stock(self):
        payload = self.get_valid_payload()
        payload["products_list"][0]["quantity"] = 999

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_denomination(self):
        payload = self.get_valid_payload()
        payload["denominations"]["999"] = 1

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_negative_denomination_count(self):
        payload = self.get_valid_payload()
        payload["denominations"]["10"] = -1

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_insufficient_payment(self):
        payload = self.get_valid_payload()
        payload["amount_paid"] = "1.00"

        response = self.client.post(
            "/generate-bill/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_purchase_history_success(self):
        self.client.post(
            "/generate-bill/",
            self.get_valid_payload(),
            format="json",
        )

        response = self.client.get(
            "/bills/customer/test@example.com/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_purchase_history_empty(self):
        response = self.client.get(
            "/bills/customer/none@example.com/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_bill_detail_success(self):
        create_response = self.client.post(
            "/generate-bill/",
            self.get_valid_payload(),
            format="json",
        )

        invoice_id = create_response.data["invoice_id"]

        response = self.client.get(
            f"/bills/{invoice_id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["invoice_id"],
            invoice_id,
        )

    def test_bill_detail_not_found(self):
        response = self.client.get(
            "/bills/INVALID123/"
        )

        self.assertEqual(response.status_code, 404)
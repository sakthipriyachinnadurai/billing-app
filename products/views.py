import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import BillHistory, Product
from .serializers import BillSerializer
from .tasks import send_bill_email_task
from .utils import get_change_breakdown

logger = logging.getLogger(__name__)

class GenerateBillView(APIView):
    """ Create bill, update stock, persist history, queue invoice email """

    @transaction.atomic
    def post(self, request):
        logger.info("Generate bill request received.")

        serializer = BillSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(
                "Bill validation failed: %s",
                serializer.errors,
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        invoice_id = f"INV{timezone.now().strftime('%Y%m%d%H%M%S')}"
        email = data["customer_email"]
        products = data["products_list"]
        paid = data["amount_paid"]
        product_ids = [p["product_id"] for p in products]

        logger.info(
            "Validated bill request for %s with invoice %s",
            email,
            invoice_id,
        )

        # Lock product rows so two requests cannot oversell the same stock.
        db_products = Product.objects.select_for_update().filter(
            product_id__in=product_ids
        )
        product_map = {p.product_id: p for p in db_products}

        detailed = []
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")

        for item in products:
            p = product_map[item["product_id"]]
            qty = item["quantity"]

            if qty > p.stock:
                logger.warning(
                    "Stock changed before billing for %s",
                    p.product_id,
                )
                raise ValidationError(
                    {
                        "detail": (
                            f"Insufficient stock for {p.product_id} "
                            "(it may have changed). Please retry."
                        )
                    }
                )

            unit_price = Decimal(str(p.price))
            tax_rate = Decimal(str(p.tax_rate))
            purchase_price = unit_price * qty
            tax_amount = (purchase_price * tax_rate) / Decimal("100")
            total_price = purchase_price + tax_amount

            subtotal += purchase_price
            total_tax += tax_amount
            p.stock -= qty

            detailed.append({
                "product_id": p.product_id,
                "name": p.name,
                "quantity": qty,
                "unit_price": float(unit_price),
                "purchase_price": float(purchase_price),
                "tax_rate": float(tax_rate),
                "tax_amount": float(round(tax_amount, 2)),
                "total_price": float(round(total_price, 2)),
            })

        Product.objects.bulk_update(db_products, ["stock"])

        total_amount = subtotal + total_tax
        balance = paid - total_amount

        bill = BillHistory.objects.create(
            invoice_id=invoice_id,
            customer_email=email,
            products_list=detailed,
            total_amount=total_amount,
            amount_received=paid,
            balance_amount=balance,
        )

        logger.info(
            "Bill saved successfully: %s for %s",
            invoice_id,
            email,
        )

        # Change uses drawer counts from request.
        change_breakdown = get_change_breakdown(
            balance,
            data["denominations"],
        )

        email_line_items = [
            {
                "product_id": row["product_id"],
                "product_name": row["name"],
                "unit_price": row["unit_price"],
                "quantity": row["quantity"],
                "tax_amount": row["tax_amount"],
                "total_price": row["total_price"],
            }
            for row in detailed
        ]

        # Queue email task after transaction commits
        send_bill_email_task.delay(
            email,
            {
                "invoice_id": invoice_id,
                "customer_email": email,
                "transaction_time": bill.transaction_time.isoformat(),
                "products_list": email_line_items,
                "subtotal": float(round(subtotal, 2)),
                "total_tax": float(round(total_tax, 2)),
                "total_amount": str(total_amount),
                "amount_paid": str(paid),
                "balance_amount": str(balance),
            },
        )

        logger.info(
            "Invoice email task queued for %s (%s)",
            email,
            invoice_id,
        )

        return Response(
            {
                "message": "Bill generated",
                "invoice_id": invoice_id,
                "customer_email": email,
                "transaction_time": bill.transaction_time,
                "products_list": detailed,
                "subtotal": float(round(subtotal, 2)),
                "total_tax": float(round(total_tax, 2)),
                "total_amount": float(round(total_amount, 2)),
                "amount_paid": paid,
                "balance_amount": float(round(balance, 2)),
                "change_breakdown": change_breakdown,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomerPurchaseListView(APIView):
    """List bills for a customer email."""

    def get(self, request, email):
        logger.info(
            "Fetching purchase history for %s",
            email,
        )

        bills = BillHistory.objects.filter(
            customer_email=email
        ).order_by("-transaction_time")

        logger.info(
            "Found %s bills for %s",
            bills.count(),
            email,
        )

        return Response(
            [
                {
                    "invoice_id": b.invoice_id,
                    "total_amount": str(b.total_amount),
                    "amount_paid": str(b.amount_received),
                    "balance_amount": str(b.balance_amount),
                    "transaction_time": b.transaction_time,
                }
                for b in bills
            ],
            status=status.HTTP_200_OK,
        )


class BillDetailView(APIView):
    """Return one saved invoice."""

    def get(self, request, invoice_id):
        logger.info(
            "Fetching bill detail for %s",
            invoice_id,
        )

        try:
            bill = BillHistory.objects.get(
                invoice_id=invoice_id
            )
        except BillHistory.DoesNotExist:
            logger.warning(
                "Bill not found: %s",
                invoice_id,
            )
            return Response(
                {"error": "Bill not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        lines = bill.products_list or []

        subtotal = sum(
            Decimal(str(x.get("purchase_price", 0)))
            for x in lines
        )
        total_tax = sum(
            Decimal(str(x.get("tax_amount", 0)))
            for x in lines
        )

        change_breakdown = get_change_breakdown(
            bill.balance_amount
        )

        logger.info(
            "Bill detail returned for %s",
            invoice_id,
        )

        return Response(
            {
                "invoice_id": bill.invoice_id,
                "customer_email": bill.customer_email,
                "products_list": bill.products_list,
                "subtotal": float(round(subtotal, 2)),
                "total_tax": float(round(total_tax, 2)),
                "total_amount": str(bill.total_amount),
                "amount_paid": str(bill.amount_received),
                "balance_amount": str(bill.balance_amount),
                "transaction_time": bill.transaction_time,
                "change_breakdown": change_breakdown,
            },
            status=status.HTTP_200_OK,
        )
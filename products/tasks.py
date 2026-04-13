"""Async Celery jobs. Failures are logged """
import logging
from celery import shared_task
from .utils import send_bill_email

logger = logging.getLogger(__name__)


@shared_task
def send_bill_email_task(email, context):
    logger.info(
        "Task started: invoice email for %s (%s)",
        email,
        context.get("invoice_id"),
    )
    try:
        send_bill_email(email, context)
        logger.info(
            "Invoice email sent: %s invoice %s",
            email,
            context.get("invoice_id"),
        )
    except Exception:
        logger.exception("Invoice email failed for %s", email)
        raise

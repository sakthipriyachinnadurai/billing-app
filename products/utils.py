"""Change calculation (greedy) and HTML invoice email."""
import logging
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def get_change_breakdown(balance_amount, available=None):
    denominations = sorted(
        [int(d) for d in settings.ACCEPTED_DENOMINATIONS],
        reverse=True,
    )

    d = Decimal(str(balance_amount))
    remaining = int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if remaining <= 0:
        return {}

    change = {}

    if available is None:
        for note in denominations:
            if remaining <= 0:
                break
            count = remaining // note
            if count > 0:
                change[str(note)] = count
                remaining %= note
        return change

    inv = {
        str(n): int(available.get(str(n), 0))
        for n in settings.ACCEPTED_DENOMINATIONS
    }

    for note in denominations:
        if remaining <= 0:
            break
        key = str(note)
        need = remaining // note
        have = inv.get(key, 0)
        take = min(need, have)
        if take > 0:
            change[key] = take
            remaining -= take * note
            inv[key] = have - take

    if remaining != 0:
        approx = int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        raise ValueError(
            "Cannot make exact change with the note counts in the drawer "
            f"(balance to return is about INR {approx} in whole rupees). "
            "Add smaller notes or adjust drawer counts."
        )

    return change


def send_bill_email(to_email, context):
    """Send multipart email using products/templates/invoice.html."""
    subject = f"Invoice {context['invoice_id']}"
    html_content = render_to_string("invoice.html", context)
    from_email = settings.DEFAULT_FROM_EMAIL
    logger.info(
        "Invoice email: to=%s backend=%s from=%s",
        to_email,
        settings.EMAIL_BACKEND,
        from_email,
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body="Your invoice is attached in HTML format.",
        from_email=from_email,
        to=[to_email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)

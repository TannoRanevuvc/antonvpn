"""Robokassa payment link builder."""
from urllib.parse import urlencode

from config import settings
from .verification import build_signature_init


def create_invoice_url(inv_id: int, amount_rub: float, description: str = "Пополнение баланса") -> str:
    """
    Build a Robokassa payment URL for the given invoice.
    Uses the standard payment page (not API, no pre-registration required).
    """
    out_sum = f"{amount_rub:.2f}"
    signature = build_signature_init(out_sum, str(inv_id), settings.PASS1)

    params = {
        "MrchLogin": settings.SHOP_IND,
        "OutSum": out_sum,
        "InvId": inv_id,
        "Description": description,
        "SignatureValue": signature,
        "Encoding": "utf-8",
    }
    if settings.ROBOKASSA_IS_TEST:
        params["IsTest"] = 1

    base = "https://auth.robokassa.ru/Merchant/Index.aspx"
    return f"{base}?{urlencode(params)}"

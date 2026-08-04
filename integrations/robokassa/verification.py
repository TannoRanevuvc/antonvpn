import hashlib

from config import settings
from .exceptions import RobokassaSignatureError


def _md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest().upper()


def build_signature_result(out_sum: str, inv_id: str, password2: str) -> str:
    """Signature for ResultURL callback: md5(OutSum:InvId:Pass2)."""
    return _md5(f"{out_sum}:{inv_id}:{password2}")


def build_signature_init(out_sum: str, inv_id: str, password1: str) -> str:
    """Signature for payment initiation."""
    return _md5(f"{settings.SHOP_IND}:{out_sum}:{inv_id}:{password1}")


def verify_result_signature(out_sum: str, inv_id: str, signature: str) -> bool:
    """Verify the signature from Robokassa ResultURL callback."""
    expected = build_signature_result(out_sum, inv_id, settings.PASS2)
    return expected == signature.upper()


def assert_result_signature(out_sum: str, inv_id: str, signature: str) -> None:
    if not verify_result_signature(out_sum, inv_id, signature):
        raise RobokassaSignatureError("Invalid Robokassa result signature")

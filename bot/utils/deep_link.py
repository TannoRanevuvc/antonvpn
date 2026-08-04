"""Deep-link builders and parsers."""
from config import settings


def gift_start_payload(activation_code: str) -> str:
    return f"gift_{activation_code}"


def referral_start_payload(ref_code: str) -> str:
    return f"ref_{ref_code}"


def gift_link(activation_code: str) -> str:
    bot_link = settings.BOT_LINK.rstrip("/")
    return f"{bot_link}?start={gift_start_payload(activation_code)}"


def referral_link(ref_code: str) -> str:
    bot_link = settings.BOT_LINK.rstrip("/")
    return f"{bot_link}?start={referral_start_payload(ref_code)}"


def parse_start_payload(payload: str | None) -> tuple[str, str]:
    """Returns (type, value) where type is 'gift', 'ref', or ''."""
    if not payload:
        return "", ""
    if payload.startswith("gift_"):
        return "gift", payload[5:]
    if payload.startswith("ref_"):
        return "ref", payload[4:]
    return "", payload

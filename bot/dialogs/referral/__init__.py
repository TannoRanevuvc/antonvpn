from aiogram_dialog import Dialog
from .windows import build_referral_window


def create_referral_dialog() -> Dialog:
    return Dialog(build_referral_window())

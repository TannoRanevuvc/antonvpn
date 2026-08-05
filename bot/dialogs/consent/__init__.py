from aiogram_dialog import Dialog
from .windows import build_consent_window


def create_consent_dialog() -> Dialog:
    return Dialog(build_consent_window())

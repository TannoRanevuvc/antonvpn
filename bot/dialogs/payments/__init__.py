from aiogram_dialog import Dialog
from .windows import build_payments_windows


def create_payments_dialog() -> Dialog:
    return Dialog(*build_payments_windows())

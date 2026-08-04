from aiogram_dialog import Dialog
from .windows import build_subscriptions_windows


def create_subscriptions_dialog() -> Dialog:
    return Dialog(*build_subscriptions_windows())

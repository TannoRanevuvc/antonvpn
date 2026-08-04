from aiogram_dialog import Dialog
from .windows import build_notification_windows


def create_notifications_dialog() -> Dialog:
    return Dialog(*build_notification_windows())

from aiogram_dialog import Dialog
from .windows import build_gift_activate_windows, build_gifts_windows


def create_gifts_dialog() -> Dialog:
    return Dialog(*build_gifts_windows())


def create_gift_activate_dialog() -> Dialog:
    return Dialog(*build_gift_activate_windows())

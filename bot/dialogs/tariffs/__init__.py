from aiogram_dialog import Dialog
from .windows import build_tariff_windows


def create_tariffs_dialog() -> Dialog:
    return Dialog(*build_tariff_windows())

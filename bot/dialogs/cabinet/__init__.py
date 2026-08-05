from aiogram_dialog import Dialog
from .windows import build_cabinet_window, build_oferta_window


def create_cabinet_dialog() -> Dialog:
    return Dialog(build_cabinet_window())


def create_oferta_dialog() -> Dialog:
    return Dialog(build_oferta_window())

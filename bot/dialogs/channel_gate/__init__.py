from aiogram_dialog import Dialog
from .windows import build_channel_gate_window


def create_channel_gate_dialog() -> Dialog:
    return Dialog(build_channel_gate_window())

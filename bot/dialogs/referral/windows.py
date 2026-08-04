from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format

from bot.states import CabinetSG, ReferralSG
from .getters import referral_getter


def build_referral_window() -> Window:
    return Window(
        Format("{text}"),
        Button(Format("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=ReferralSG.INFO,
        getter=referral_getter,
        parse_mode="HTML",
    )

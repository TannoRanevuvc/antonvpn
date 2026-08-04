from aiogram import types
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Url
from aiogram_dialog.widgets.text import Const, Format

from bot.states import CabinetSG, PaymentsSG
from .getters import topup_amount_getter, topup_confirm_getter, topup_success_getter


async def on_amount_entered(message: types.Message, widget, manager: DialogManager, text: str) -> None:
    try:
        amount = float(text.replace(",", "."))
        if amount < 100:
            await message.answer("Минимальная сумма — 100₽. Попробуйте снова.")
            return
    except ValueError:
        await message.answer("Введите числовое значение.")
        return

    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")

    from services.payment_service import PaymentService
    svc = PaymentService(session)
    topup, payment_url = await svc.create_topup_invoice(user, amount)

    manager.dialog_data["amount"] = amount
    manager.dialog_data["topup_id"] = topup.id
    manager.dialog_data["payment_url"] = payment_url

    await manager.switch_to(PaymentsSG.CONFIRM)


def build_payments_windows() -> list[Window]:
    amount_window = Window(
        Format("{text}"),
        TextInput(id="amount_input", on_success=on_amount_entered),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=PaymentsSG.TOPUP_AMOUNT,
        getter=topup_amount_getter,
        parse_mode="HTML",
    )

    confirm_window = Window(
        Format("{text}"),
        Url(Const("💳 Оплатить через Robokassa"), url=Format("{payment_url}")),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.switch_to(PaymentsSG.TOPUP_AMOUNT)),
        state=PaymentsSG.CONFIRM,
        getter=topup_confirm_getter,
        parse_mode="HTML",
    )

    success_window = Window(
        Format("{text}"),
        Button(Const("🏠 В кабинет"), id="home", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=PaymentsSG.SUCCESS,
        getter=topup_success_getter,
    )

    return [amount_window, confirm_window, success_window]

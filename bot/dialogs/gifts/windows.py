from aiogram import types
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column, Select
from aiogram_dialog.widgets.text import Const, Format

from bot.states import CabinetSG, GiftActivateSG, GiftsSG
from .getters import gift_activate_getter, gift_confirm_getter, gift_sent_getter, gift_success_getter, gift_tariff_getter


async def on_tariff_selected(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str) -> None:
    manager.dialog_data["tariff_id"] = item_id
    await manager.switch_to(GiftsSG.CONFIRM)


async def on_gift_confirm(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    tariff_id = manager.dialog_data.get("tariff_id")

    from services.gift_service import GiftService, GiftError
    from services.user_service import InsufficientBalanceError
    svc = GiftService(session)
    try:
        gift = await svc.create_gift(user, int(tariff_id))
        manager.dialog_data["gift_code"] = gift.activation_code
        await manager.switch_to(GiftsSG.SENT)
    except InsufficientBalanceError:
        await callback.answer("❌ Недостаточно средств.", show_alert=True)
    except GiftError as exc:
        await callback.answer(str(exc), show_alert=True)


async def on_gift_activate(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    code = manager.dialog_data.get("gift_code")

    from services.gift_service import GiftService, GiftError
    svc = GiftService(session)
    try:
        await svc.activate_gift(code, user)
        await manager.switch_to(GiftActivateSG.SUCCESS)
    except GiftError as exc:
        await callback.answer(str(exc), show_alert=True)


def build_gifts_windows() -> list[Window]:
    tariff_window = Window(
        Format("{text}"),
        Column(
            Select(
                Format("{item[0]}"),
                id="gift_tariff",
                item_id_getter=lambda x: x[1],
                items="tariff_items",
                on_click=on_tariff_selected,
            ),
            when="has_tariffs",
        ),
        Const("Тарифы недоступны.", when=lambda d, w, m: not d.get("has_tariffs")),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=GiftsSG.TARIFF_SELECT,
        getter=gift_tariff_getter,
        parse_mode="HTML",
    )

    confirm_window = Window(
        Format("{text}"),
        Button(Const("✅ Подарить"), id="confirm", on_click=on_gift_confirm, when="can_buy"),
        Const("❌ Недостаточно средств.", when=lambda d, w, m: not d.get("can_buy")),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.switch_to(GiftsSG.TARIFF_SELECT)),
        state=GiftsSG.CONFIRM,
        getter=gift_confirm_getter,
        parse_mode="HTML",
    )

    sent_window = Window(
        Format("{text}"),
        Button(Const("🏠 В кабинет"), id="home", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=GiftsSG.SENT,
        getter=gift_sent_getter,
        parse_mode="HTML",
    )

    return [tariff_window, confirm_window, sent_window]


def build_gift_activate_windows() -> list[Window]:
    activate_window = Window(
        Format("{text}"),
        Button(Const("🎁 Активировать"), id="activate", on_click=on_gift_activate, when="can_activate"),
        Button(Const("⬅️ Отмена"), id="cancel", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=GiftActivateSG.ACTIVATE,
        getter=gift_activate_getter,
        parse_mode="HTML",
    )

    success_window = Window(
        Format("{text}"),
        Button(Const("📱 Мои подписки"), id="subs", on_click=lambda c, b, m: None),
        Button(Const("🏠 В кабинет"), id="home", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=GiftActivateSG.SUCCESS,
        getter=gift_success_getter,
    )

    return [activate_window, success_window]

from aiogram import types
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from bot.states import CabinetSG, TariffsSG
from database.models.subscription import TariffType
from .getters import tariff_confirm_getter, tariff_list_getter, tariff_type_getter


async def on_vpn_type(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["tariff_type"] = TariffType.VPN.value
    await manager.switch_to(TariffsSG.LIST)


async def on_obfs_type(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["tariff_type"] = TariffType.OBFUSCATED.value
    await manager.switch_to(TariffsSG.LIST)


async def on_tariff_selected(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str) -> None:
    manager.dialog_data["tariff_id"] = item_id
    await manager.switch_to(TariffsSG.CONFIRM)


async def on_buy_confirm(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    tariff_id = manager.dialog_data.get("tariff_id")

    from services.subscription_service import SubscriptionService
    from services.user_service import InsufficientBalanceError
    svc = SubscriptionService(session)
    try:
        await svc.create(user, int(tariff_id))
        await callback.answer("✅ Подписка успешно создана!", show_alert=True)
        await manager.start(CabinetSG.MAIN)
    except InsufficientBalanceError:
        await callback.answer("❌ Недостаточно средств на балансе.", show_alert=True)
    except Exception as exc:
        await callback.answer(f"Ошибка: {exc}", show_alert=True)


def build_tariff_windows() -> list[Window]:
    type_window = Window(
        Const("🔌 Выберите тип подписки:"),
        Row(
            Button(Const("🔒 VPN"), id="vpn", on_click=on_vpn_type),
            Button(Const("🛡 Обход глушилок"), id="obfs", on_click=on_obfs_type),
        ),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=TariffsSG.TYPE_SELECT,
        getter=tariff_type_getter,
    )

    list_window = Window(
        Format("{text}"),
        Column(
            Select(
                Format("{item[0]}"),
                id="tariff_select",
                item_id_getter=lambda x: x[1],
                items="tariff_items",
                on_click=on_tariff_selected,
            ),
            when="has_tariffs",
        ),
        Const("Тарифы недоступны.", when=lambda d, w, m: not d.get("has_tariffs")),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.switch_to(TariffsSG.TYPE_SELECT)),
        state=TariffsSG.LIST,
        getter=tariff_list_getter,
        parse_mode="HTML",
    )

    confirm_window = Window(
        Format("{text}"),
        Button(Const("✅ Купить"), id="buy", on_click=on_buy_confirm, when="can_buy"),
        Button(Const("💳 Пополнить баланс"), id="topup", on_click=lambda c, b, m: None, when=lambda d, w, m: not d.get("can_buy")),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.switch_to(TariffsSG.LIST)),
        state=TariffsSG.CONFIRM,
        getter=tariff_confirm_getter,
        parse_mode="HTML",
    )

    return [type_window, list_window, confirm_window]

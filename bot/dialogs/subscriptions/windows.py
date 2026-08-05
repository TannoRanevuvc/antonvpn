from aiogram import types
from aiogram.types import WebAppInfo
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, Row, Select, SwitchTo, WebApp
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from bot.states import CabinetSG, SubscriptionsSG, TariffsSG
from .getters import devices_getter, subscription_detail_getter, subscriptions_list_getter


async def on_sub_selected(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str) -> None:
    manager.dialog_data["sub_id"] = item_id
    await manager.switch_to(SubscriptionsSG.DETAIL)


async def on_send_sub_url(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    sub_url = manager.dialog_data.get("sub_url") or manager.middleware_data.get("sub_url")
    if not sub_url:
        # Fetch from DB
        session = manager.middleware_data.get("session")
        user = manager.middleware_data.get("user")
        sub_id = manager.dialog_data.get("sub_id")
        from database.repositories import SubscriptionRepository
        sub = await SubscriptionRepository(session).get_by_id_and_user(int(sub_id), user.id)
        sub_url = sub.remna_sub_url if sub else None

    if not sub_url:
        await callback.answer("Ссылка подписки недоступна.", show_alert=True)
        return

    await callback.message.answer(
        f"🔗 <b>Ссылка для VPN-клиента:</b>\n<code>{sub_url}</code>",
        parse_mode="HTML",
    )
    await callback.answer()


async def on_device_delete(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    sub_id = manager.dialog_data.get("sub_id")

    from database.repositories import SubscriptionRepository
    from services.subscription_service import SubscriptionService
    repo = SubscriptionRepository(session)
    sub = await repo.get_by_id_and_user(int(sub_id), user.id)
    if sub:
        svc = SubscriptionService(session)
        await svc.delete_device(sub, user.id, item_id)
    await manager.show()


async def on_rename_done(message: types.Message, widget, manager: DialogManager, text: str) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    sub_id = manager.dialog_data.get("sub_id")

    from database.repositories import SubscriptionRepository
    from services.subscription_service import SubscriptionService
    repo = SubscriptionRepository(session)
    sub = await repo.get_by_id_and_user(int(sub_id), user.id)
    if sub:
        svc = SubscriptionService(session)
        await svc.rename(sub, user.id, text[:64])

    await manager.switch_to(SubscriptionsSG.DETAIL)


async def on_toggle_auto_renewal(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    sub_id = manager.dialog_data.get("sub_id")

    from database.repositories import SubscriptionRepository
    from services.subscription_service import SubscriptionService
    repo = SubscriptionRepository(session)
    sub = await repo.get_by_id_and_user(int(sub_id), user.id)
    if sub:
        svc = SubscriptionService(session)
        await svc.toggle_auto_renewal(sub, user.id)
    await manager.show()


def build_subscriptions_windows() -> list[Window]:
    list_window = Window(
        DynamicMedia("image_path", when="image_path"),
        Format("{text}"),
        Column(
            Select(
                Format("{item[0]}"),
                id="sub_select",
                item_id_getter=lambda x: x[1],
                items="subscriptions",
                on_click=on_sub_selected,
            ),
            when="has_subscriptions",
        ),
        Const("У вас нет подписок.", when=lambda d, w, m: not d.get("has_subscriptions")),
        Button(Const("➕ Создать подписку"), id="create_sub", on_click=lambda c, b, m: m.start(TariffsSG.TYPE_SELECT)),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=SubscriptionsSG.LIST,
        getter=subscriptions_list_getter,
        parse_mode="HTML",
    )

    detail_window = Window(
        DynamicMedia("image_path", when="image_path"),
        Format("{text}"),
        Row(
            WebApp(
                Const("🌐 Открыть подписку"),
                url=Format("{sub_url}"),
                id="open_sub",
                when="sub_url",
            ),
            Button(Const("📱 Устройства"), id="devices", on_click=lambda c, b, m: m.switch_to(SubscriptionsSG.DEVICES)),
        ),
        Button(
            Const("📋 Ссылка для VPN-клиента"),
            id="send_url",
            on_click=on_send_sub_url,
            when="sub_url",
        ),
        Row(
            Button(Const("🔄 Продлить"), id="renew", on_click=lambda c, b, m: m.start(TariffsSG.TYPE_SELECT)),
            Button(Const("✏️ Переименовать"), id="rename", on_click=lambda c, b, m: m.switch_to(SubscriptionsSG.RENAME)),
        ),
        Button(
            Format("🔁 Автопродление: {auto_renewal}"),
            id="auto_renewal",
            on_click=on_toggle_auto_renewal,
        ),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.switch_to(SubscriptionsSG.LIST)),
        state=SubscriptionsSG.DETAIL,
        getter=subscription_detail_getter,
        parse_mode="HTML",
    )

    devices_window = Window(
        Const("<b>📱 Устройства подписки</b>"),
        Format("Всего: {device_count}/{max_devices}\n\n{text}"),
        Column(
            Select(
                Format("🗑 {item[0]}"),
                id="del_device",
                item_id_getter=lambda x: x[1],
                items="device_items",
                on_click=on_device_delete,
            ),
        ),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.switch_to(SubscriptionsSG.DETAIL)),
        state=SubscriptionsSG.DEVICES,
        getter=devices_getter,
        parse_mode="HTML",
    )

    rename_window = Window(
        Const("✏️ Введите новое название подписки (до 64 символов):"),
        TextInput(id="rename_input", on_success=on_rename_done),
        Button(Const("⬅️ Отмена"), id="back", on_click=lambda c, b, m: m.switch_to(SubscriptionsSG.DETAIL)),
        state=SubscriptionsSG.RENAME,
    )

    return [list_window, detail_window, devices_window, rename_window]

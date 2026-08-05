from aiogram import types
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format

from bot.states import CabinetSG, GiftsSG, OfertaSG, PaymentsSG, ReferralSG, SubscriptionsSG
from .getters import cabinet_getter, oferta_getter


async def on_language_toggle(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    from services.user_service import UserService
    svc = UserService(session)
    new_lang = "en" if user.language_code == "ru" else "ru"
    await svc.update_language(user, new_lang)
    manager.middleware_data["user"] = await svc.get_by_chat_id(user.chat_id)
    await manager.show()


def build_cabinet_window() -> Window:
    return Window(
        DynamicMedia("image_path", when="image_path"),
        Format("{text}"),
        Row(
            Button(Format("📱 Подписки"), id="subs", on_click=lambda c, b, m: m.start(SubscriptionsSG.LIST)),
            Button(Format("💳 Баланс"), id="balance", on_click=lambda c, b, m: m.start(PaymentsSG.TOPUP_AMOUNT)),
        ),
        Row(
            Button(Format("🎁 Подарок"), id="gift", on_click=lambda c, b, m: m.start(GiftsSG.TARIFF_SELECT)),
            Button(Format("👥 Рефералы"), id="ref", on_click=lambda c, b, m: m.start(ReferralSG.INFO)),
        ),
        Row(
            Url(Format("🌐 Сайт"), url=Format("{site_url}"), when="site_url"),
            Url(Format("📢 Канал"), url=Format("{news_channel_url}"), when="news_channel_url"),
        ),
        Row(
            Url(Format("💬 Поддержка"), url=Format("{support_url}"), when="support_url"),
            Button(Format("🌍 Язык/Language"), id="lang", on_click=on_language_toggle),
        ),
        Button(Format("📄 Оферта"), id="oferta", on_click=lambda c, b, m: m.start(OfertaSG.VIEW)),
        state=CabinetSG.MAIN,
        getter=cabinet_getter,
        parse_mode="HTML",
    )


def build_oferta_window() -> Window:
    return Window(
        DynamicMedia("image_path", when="image_path"),
        Format("{text}"),
        Button(Format("« Назад"), id="back", on_click=lambda c, b, m: m.start(CabinetSG.MAIN)),
        state=OfertaSG.VIEW,
        getter=oferta_getter,
        parse_mode="HTML",
    )

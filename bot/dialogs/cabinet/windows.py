from aiogram import types
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format

from bot.states import CabinetSG, GiftsSG, PaymentsSG, ReferralSG, SubscriptionsSG
from .getters import cabinet_getter


async def on_language_toggle(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    from services.user_service import UserService
    svc = UserService(session)
    new_lang = "en" if user.language_code == "ru" else "ru"
    await svc.update_language(user, new_lang)
    manager.middleware_data["user"] = await svc.get_by_chat_id(user.chat_id)
    await manager.show()


async def on_trial_click(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    from database.repositories import BotSettingsRepository
    from services.subscription_service import SubscriptionService, TrialNotAvailableError
    bot_settings = await BotSettingsRepository(session).get()
    svc = SubscriptionService(session)
    try:
        sub = await svc.create_trial(user, bot_settings)
        days = bot_settings.trial_days if bot_settings else 0
        await callback.answer(f"✅ Пробный период на {days} дней активирован!", show_alert=True)
        await manager.show()
    except TrialNotAvailableError as e:
        await callback.answer(f"❌ {e}", show_alert=True)
    except Exception as exc:
        await callback.answer(f"Ошибка: {exc}", show_alert=True)


async def on_oferta_click(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    from database.repositories import BotSettingsRepository
    bot_settings = await BotSettingsRepository(session).get()
    file_path = bot_settings.oferta_file_path if bot_settings else None
    if not file_path:
        await callback.answer("Файл оферты не загружен.", show_alert=True)
        return
    import os
    if not os.path.exists(file_path):
        await callback.answer("Файл оферты не найден на сервере.", show_alert=True)
        return
    from aiogram.types import FSInputFile
    await callback.message.answer_document(
        FSInputFile(file_path),
        caption="📄 Оферта",
    )
    await callback.answer()


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
        Button(
            Format("🎯 Пробный период ({trial_days} дн.)"),
            id="trial",
            on_click=on_trial_click,
            when="trial_eligible",
        ),
        Button(Format("📄 Оферта"), id="oferta", on_click=on_oferta_click),
        state=CabinetSG.MAIN,
        getter=cabinet_getter,
        parse_mode="HTML",
    )

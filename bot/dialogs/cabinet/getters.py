from aiogram_dialog import DialogManager

from bot.utils.message_builder import build_payload_by_key
from database.repositories import BotSettingsRepository, SubscriptionRepository


async def oferta_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    payload = await build_payload_by_key("OFERTA", session)
    return {"text": payload["text"], "image_path": payload["image_path"]}


async def cabinet_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")

    payload = await build_payload_by_key("CABINET", session)
    bot_settings = await BotSettingsRepository(session).get()
    sub_repo = SubscriptionRepository(session)
    subs = await sub_repo.get_by_user_id(user.id)

    balance = float(user.balance_rub)
    sub_count = len(subs)

    text = payload["text"].format(
        first_name=user.first_name or "Пользователь",
        telegram_id=user.telegram_id,
        balance=f"{balance:.2f}",
        sub_count=sub_count,
    )

    return {
        "text": text,
        "image_path": payload["image_path"],
        "site_url": bot_settings.site_url if bot_settings else "",
        "news_channel_url": bot_settings.news_channel_url if bot_settings else "",
        "support_url": bot_settings.support_url if bot_settings else "",
        "language_code": user.language_code,
    }

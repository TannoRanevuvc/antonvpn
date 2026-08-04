from aiogram import types, Bot
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Url
from aiogram_dialog.widgets.text import Format

from bot.states import CabinetSG, ChannelGateSG


async def channel_gate_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    from database.repositories.settings import ChannelSettingsRepository
    settings = await ChannelSettingsRepository(session).get()
    channel_url = settings.channel_url if settings else ""
    return {
        "text": "📢 Для использования бота необходимо подписаться на наш канал.",
        "channel_url": channel_url or "https://t.me/",
    }


async def on_check_again(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")
    bot: Bot = manager.middleware_data.get("bot")

    from services.user_service import UserService
    svc = UserService(session)
    is_member = await svc.check_channel_membership(user, bot)

    if is_member:
        await manager.start(CabinetSG.MAIN)
    else:
        await callback.answer("Вы ещё не подписались на канал.", show_alert=True)


def build_channel_gate_window() -> Window:
    return Window(
        Format("{text}"),
        Url(Format("📢 Подписаться на канал"), url=Format("{channel_url}")),
        Button(Format("✅ Проверить подписку"), id="check", on_click=on_check_again),
        state=ChannelGateSG.CHECK,
        getter=channel_gate_getter,
        parse_mode="HTML",
    )

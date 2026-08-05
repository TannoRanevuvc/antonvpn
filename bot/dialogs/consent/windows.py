from urllib.parse import urlparse

from aiogram import types
from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column, Url
from aiogram_dialog.widgets.text import Const, Format

from bot.states import ChannelGateSG, ConsentSG
from config import settings as app_settings


def _site_base() -> str:
    parsed = urlparse(app_settings.ADMIN_PUBLIC_BASE_URL)
    return f"{parsed.scheme}://{parsed.netloc}"


async def consent_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    base = _site_base()

    oferta_url = None
    try:
        from database.repositories import BotSettingsRepository
        bot_settings = await BotSettingsRepository(session).get()
        if bot_settings and bot_settings.oferta_file_path:
            rel = bot_settings.oferta_file_path.lstrip("/")
            oferta_url = f"{base}/{rel}"
    except Exception:
        pass

    return {
        "base": base,
        "oferta_url": oferta_url,
        "has_oferta": bool(oferta_url),
    }


async def on_agree(callback: types.CallbackQuery, button: Button, manager: DialogManager) -> None:
    session = manager.middleware_data.get("session")
    user = manager.middleware_data.get("user")

    from services.user_service import UserService
    svc = UserService(session)
    user = await svc.give_consent(user)
    manager.middleware_data["user"] = user

    # After consent — check channel subscription
    bot = manager.middleware_data.get("bot")
    if bot:
        is_member = await svc.check_channel_membership(user, bot)
        if not is_member:
            from database.repositories import ChannelSettingsRepository
            ch = await ChannelSettingsRepository(session).get()
            if ch and ch.is_enabled:
                await manager.start(ChannelGateSG.CHECK)
                return

    from bot.states import CabinetSG
    await manager.start(CabinetSG.MAIN)


def build_consent_window() -> Window:
    return Window(
        Const(
            "👋 <b>Добро пожаловать в AntonVPN!</b>\n\n"
            "Продолжая использование сервиса, вы подтверждаете, что ознакомились и соглашаетесь с:"
        ),
        Column(
            Url(
                Const("📄 Пользовательское соглашение"),
                url=Format("{base}/document/user-agreement"),
            ),
            Url(
                Const("🔒 Политика конфиденциальности"),
                url=Format("{base}/document/privacy-policy"),
            ),
            Url(
                Const("💰 Политика возврата средств"),
                url=Format("{base}/document/refund-policy"),
            ),
            Url(
                Const("📋 Оферта"),
                url=Format("{oferta_url}"),
                when="has_oferta",
            ),
        ),
        Button(
            Const("✅ Соглашаюсь и продолжить"),
            id="consent_agree",
            on_click=on_agree,
        ),
        state=ConsentSG.AGREE,
        getter=consent_getter,
        parse_mode="HTML",
    )

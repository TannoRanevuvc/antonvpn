"""
Load/create the user from DB, enforce consent gate, then channel subscription gate.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from aiogram_dialog import DialogManager, StartMode

from bot.states import ChannelGateSG, ConsentSG
from database.repositories import UserRepository
from services.user_service import UserService
from config import logger


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = data.get("session")
        if session is None:
            return await handler(event, data)

        tg_user = None
        if isinstance(event, (Message, CallbackQuery)):
            tg_user = event.from_user
        elif isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        if tg_user is None:
            return await handler(event, data)

        user_service = UserService(session)
        user, is_new = await user_service.register_or_get(
            telegram_id=tg_user.id,
            chat_id=tg_user.id,
            first_name=tg_user.first_name,
            username=tg_user.username,
            language_code=tg_user.language_code or "ru",
        )

        if user.is_banned:
            return

        await user_service.update_activity(user)
        data["user"] = user
        data["is_new_user"] = is_new

        bot: Bot | None = data.get("bot")
        if bot and not isinstance(bot, Bot):
            bot = None

        dialog_manager: DialogManager | None = data.get("dialog_manager")

        # Get current FSM state to avoid redirect loops
        fsm: FSMContext | None = data.get("state")
        current_state: str | None = None
        if fsm:
            current_state = await fsm.get_state()

        # ── Consent gate ──────────────────────────────────────────────────────
        if user.consent_at is None:
            # Allow callbacks inside the consent dialog to be handled normally
            if current_state == ConsentSG.AGREE.state:
                return await handler(event, data)

            if dialog_manager:
                try:
                    await dialog_manager.start(ConsentSG.AGREE, mode=StartMode.RESET_STACK)
                    return
                except Exception as exc:
                    logger.warning("Could not start ConsentSG: %s", exc)
            return await handler(event, data)

        # ── Channel gate ──────────────────────────────────────────────────────
        if bot and current_state != ChannelGateSG.CHECK.state:
            is_member = await user_service.check_channel_membership(user, bot)
            if not is_member:
                if dialog_manager:
                    try:
                        await dialog_manager.start(ChannelGateSG.CHECK, mode=StartMode.RESET_STACK)
                        return
                    except Exception as exc:
                        logger.warning("Could not start ChannelGateSG: %s", exc)

        return await handler(event, data)

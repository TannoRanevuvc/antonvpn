from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from bot.states import CabinetSG, ChannelGateSG, ConsentSG, GiftActivateSG
from bot.utils.deep_link import parse_start_payload
from services.referral_service import ReferralService

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager, **kwargs) -> None:
    session = kwargs.get("session")
    user = kwargs.get("user")

    # Consent gate — must be accepted before anything else
    if user and user.consent_at is None:
        await dialog_manager.start(ConsentSG.AGREE, mode=StartMode.RESET_STACK)
        return

    # Channel gate
    from aiogram import Bot
    bot: Bot = kwargs.get("bot") or dialog_manager.middleware_data.get("bot")
    if bot and session and user:
        from services.user_service import UserService
        from database.repositories import ChannelSettingsRepository
        ch = await ChannelSettingsRepository(session).get()
        if ch and ch.is_enabled:
            svc = UserService(session)
            is_member = await svc.check_channel_membership(user, bot)
            if not is_member:
                await dialog_manager.start(ChannelGateSG.CHECK, mode=StartMode.RESET_STACK)
                return

    payload = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    link_type, link_value = parse_start_payload(payload)

    if link_type == "gift" and link_value:
        await dialog_manager.start(
            GiftActivateSG.ACTIVATE,
            mode=StartMode.RESET_STACK,
            data={"gift_code": link_value},
        )
        return

    if link_type == "ref" and link_value and session and user:
        ref_svc = ReferralService(session)
        await ref_svc.register_referral(
            invited_user_id=user.id,
            ref_code=link_value,
        )

    await dialog_manager.start(CabinetSG.MAIN, mode=StartMode.RESET_STACK)

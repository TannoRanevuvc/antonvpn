from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from bot.states import CabinetSG, GiftActivateSG
from bot.utils.deep_link import parse_start_payload
from services.referral_service import ReferralService

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager, **kwargs) -> None:
    session = kwargs.get("session")
    user = kwargs.get("user")

    payload = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    link_type, link_value = parse_start_payload(payload)

    if link_type == "gift" and link_value:
        # Start gift activation dialog
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

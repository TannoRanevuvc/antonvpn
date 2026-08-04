from aiogram_dialog import DialogManager

from bot.utils.deep_link import referral_link
from database.repositories import ReferralRepository


async def referral_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")

    repo = ReferralRepository(session)
    referrals = await repo.get_all() if hasattr(repo, "get_all") else []
    my_referrals = [r for r in referrals if r.referrer_user_id == user.id]

    ref_link = referral_link(user.ref_code)

    return {
        "text": (
            f"👥 <b>Реферальная программа</b>\n\n"
            f"Ваша ссылка:\n<code>{ref_link}</code>\n\n"
            f"Приглашено: <b>{len(my_referrals)}</b> чел."
        ),
        "ref_link": ref_link,
    }

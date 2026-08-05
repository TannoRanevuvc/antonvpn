from sqlalchemy import func, select

from aiogram_dialog import DialogManager

from bot.utils.deep_link import referral_link
from database.models.referral_reward import ReferralReward
from database.models.user import Referral
from database.repositories.settings import ReferralSettingsRepository


async def referral_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data.get("session")
    user = dialog_manager.middleware_data.get("user")

    # Count direct referrals (L1)
    count_result = await session.execute(
        select(func.count()).where(Referral.referrer_user_id == user.id)
    )
    ref_count = count_result.scalar_one()

    # Total earned from all levels
    earned_result = await session.execute(
        select(func.coalesce(func.sum(ReferralReward.amount_rub), 0)).where(
            ReferralReward.beneficiary_id == user.id
        )
    )
    total_earned = float(earned_result.scalar_one())

    # Load referral settings for live conditions text
    settings_repo = ReferralSettingsRepository(session)
    settings = await settings_repo.get()
    l1_pct = int(settings.level1_percent) if settings else 15
    l2_pct = int(settings.level2_percent) if settings else 5
    max_topups = int(settings.max_paid_topups) if settings else 2

    ref_link = referral_link(user.ref_code)

    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        f"Ваша ссылка:\n<code>{ref_link}</code>\n\n"
        f"Приглашено: <b>{ref_count}</b> чел.\n"
        f"Заработано: <b>{total_earned:.2f}₽</b>\n\n"
        "<b>Условия:</b>\n"
        f"• 1-й уровень (прямые рефералы) — <b>{l1_pct}%</b> с первых <b>{max_topups}</b> пополнений\n"
        f"• 2-й уровень (рефералы ваших рефералов) — <b>{l2_pct}%</b> с первых <b>{max_topups}</b> пополнений\n\n"
        "Бонус зачисляется на баланс сразу после пополнения реферала."
    )

    return {
        "text": text,
        "ref_link": ref_link,
        "ref_count": ref_count,
        "total_earned": total_earned,
    }

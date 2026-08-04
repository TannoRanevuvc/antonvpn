from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import Referral, User
from database.repositories import ReferralRepository, UserRepository
from database.repositories.settings import ReferralSettingsRepository
from config import logger


class ReferralService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.referral_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)
        self.settings_repo = ReferralSettingsRepository(session)

    async def register_referral(
        self,
        invited_user_id: int,
        ref_code: str | None = None,
        referrer_user_id: int | None = None,
    ) -> Referral | None:
        existing = await self.referral_repo.get_by_referred_user_id(invited_user_id)
        if existing:
            return None

        if referrer_user_id is None and ref_code:
            referrer = await self.user_repo.get_by_ref_code(ref_code)
            if referrer is None:
                return None
            referrer_user_id = referrer.id

        if referrer_user_id is None or referrer_user_id == invited_user_id:
            return None

        return await self.referral_repo.create(
            referrer_user_id=referrer_user_id,
            referred_user_id=invited_user_id,
        )

    async def credit_reward(self, referred_user_id: int) -> None:
        """Credit referrer after referred user makes their first payment."""
        referral = await self.referral_repo.get_by_referred_user_id(referred_user_id)
        if referral is None or referral.reward_credited:
            return

        settings = await self.settings_repo.get()
        if settings is None or not settings.is_enabled:
            return

        referrer = await self.user_repo.get_by_id(referral.referrer_user_id)
        if referrer is None:
            return

        reward_amount = float(settings.reward_amount)
        if reward_amount <= 0:
            return

        if settings.reward_type == "balance":
            from .user_service import UserService
            user_svc = UserService(self.session)
            await user_svc.credit_balance(referrer, reward_amount)
        elif settings.reward_type == "days":
            # Extend the referrer's most recent active subscription
            from database.repositories import SubscriptionRepository
            from database.models.subscription import RemnaStatus
            from datetime import timedelta
            sub_repo = SubscriptionRepository(self.session)
            subs = await sub_repo.get_by_user_id(referrer.id)
            active = [s for s in subs if s.remna_status == RemnaStatus.ACTIVE and s.expires_at]
            if active:
                sub = active[0]
                new_expiry = sub.expires_at + timedelta(days=int(reward_amount))
                await sub_repo.update_expiry(sub, new_expiry)

        await self.referral_repo.mark_reward_credited(referral)
        logger.info("Referral reward credited: referrer=%s amount=%s type=%s", referrer.id, reward_amount, settings.reward_type)

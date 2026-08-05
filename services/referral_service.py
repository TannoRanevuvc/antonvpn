from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import Referral, User
from database.repositories import ReferralRepository, UserRepository, ReferralRewardRepository
from database.repositories.settings import ReferralSettingsRepository
from config import logger


class ReferralService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.referral_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)
        self.settings_repo = ReferralSettingsRepository(session)
        self.reward_repo = ReferralRewardRepository(session)

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

    async def credit_referral_rewards(
        self,
        payer_user_id: int,
        amount_rub: float,
        topup_id: int | None = None,
    ) -> None:
        """
        Called after a top-up is finalized.
        Credits level-1 referrer 15% and level-2 referrer 5%,
        each for at most max_paid_topups top-ups per referred user.
        """
        settings = await self.settings_repo.get()
        if settings is None or not settings.is_enabled:
            return

        l1_pct = float(settings.level1_percent)
        l2_pct = float(settings.level2_percent)
        max_topups = int(settings.max_paid_topups)

        from .user_service import UserService
        user_svc = UserService(self.session)

        # Level 1: direct referrer of the payer
        l1_referral = await self.referral_repo.get_by_referred_user_id(payer_user_id)
        if l1_referral is None:
            return

        referrer_l1 = await self.user_repo.get_by_id(l1_referral.referrer_user_id)
        if referrer_l1 is None:
            return

        l1_count = await self.reward_repo.count_rewards(
            beneficiary_id=referrer_l1.id,
            payer_id=payer_user_id,
            level=1,
        )
        if l1_count < max_topups and l1_pct > 0:
            reward_l1 = round(amount_rub * l1_pct / 100, 2)
            await user_svc.credit_balance(referrer_l1, reward_l1)
            await self.reward_repo.create_reward(
                beneficiary_id=referrer_l1.id,
                payer_id=payer_user_id,
                topup_id=topup_id,
                level=1,
                amount_rub=reward_l1,
            )
            logger.info(
                "Referral L1 reward: beneficiary=%s payer=%s amount=%.2f topup=%s",
                referrer_l1.id, payer_user_id, reward_l1, topup_id,
            )

        # Level 2: referrer of the level-1 referrer
        l2_referral = await self.referral_repo.get_by_referred_user_id(referrer_l1.id)
        if l2_referral is None:
            return

        referrer_l2 = await self.user_repo.get_by_id(l2_referral.referrer_user_id)
        if referrer_l2 is None:
            return

        l2_count = await self.reward_repo.count_rewards(
            beneficiary_id=referrer_l2.id,
            payer_id=payer_user_id,
            level=2,
        )
        if l2_count < max_topups and l2_pct > 0:
            reward_l2 = round(amount_rub * l2_pct / 100, 2)
            await user_svc.credit_balance(referrer_l2, reward_l2)
            await self.reward_repo.create_reward(
                beneficiary_id=referrer_l2.id,
                payer_id=payer_user_id,
                topup_id=topup_id,
                level=2,
                amount_rub=reward_l2,
            )
            logger.info(
                "Referral L2 reward: beneficiary=%s payer=%s amount=%.2f topup=%s",
                referrer_l2.id, payer_user_id, reward_l2, topup_id,
            )

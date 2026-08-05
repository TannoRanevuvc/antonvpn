from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.referral_reward import ReferralReward
from .base import BaseRepository


class ReferralRewardRepository(BaseRepository[ReferralReward]):
    model = ReferralReward

    async def count_rewards(self, beneficiary_id: int, payer_id: int, level: int) -> int:
        result = await self.session.execute(
            select(func.count()).where(
                ReferralReward.beneficiary_id == beneficiary_id,
                ReferralReward.payer_id == payer_id,
                ReferralReward.level == level,
            )
        )
        return result.scalar_one()

    async def create_reward(
        self,
        beneficiary_id: int,
        payer_id: int,
        topup_id: int | None,
        level: int,
        amount_rub: float,
    ) -> ReferralReward:
        reward = ReferralReward(
            beneficiary_id=beneficiary_id,
            payer_id=payer_id,
            topup_id=topup_id,
            level=level,
            amount_rub=amount_rub,
        )
        return await self.save(reward)

from datetime import datetime

from sqlalchemy import and_, select

from database.cache import GiftCache, model_to_dict
from database.models.gift import Gift, GiftStatus
from .base import BaseRepository

_GIFT_EXPIRE_DAYS = 30


class GiftRepository(BaseRepository[Gift]):
    model = Gift

    async def get_by_code(self, code: str) -> Gift | None:
        cached = await GiftCache.get(code)
        if cached:
            return Gift(**{k: v for k, v in cached.items() if k in Gift.__table__.columns.keys()})
        result = await self.session.execute(select(Gift).where(Gift.activation_code == code))
        gift = result.scalar_one_or_none()
        if gift:
            await GiftCache.set(code, model_to_dict(gift))
        return gift

    async def create(self, sender_user_id: int, tariff_id: int, amount_rub: float) -> Gift:
        from datetime import timedelta
        gift = Gift(
            sender_user_id=sender_user_id,
            tariff_id=tariff_id,
            amount_rub=amount_rub,
            expires_at=datetime.utcnow() + timedelta(days=_GIFT_EXPIRE_DAYS),
        )
        gift = await self.save(gift)
        await GiftCache.set(gift.activation_code, model_to_dict(gift))
        return gift

    async def activate(self, gift: Gift, recipient_user_id: int) -> Gift:
        # Re-fetch from DB to ensure a session-attached persistent object.
        # gift may be a transient instance reconstructed from Redis cache,
        # which would cause session.add() to attempt INSERT instead of UPDATE.
        code = gift.activation_code
        db_gift = await self.session.get(Gift, gift.id)
        if db_gift is None:
            raise ValueError(f"Gift {gift.id} not found in DB")
        db_gift.status = GiftStatus.ACTIVATED
        db_gift.recipient_user_id = recipient_user_id
        db_gift.activated_at = datetime.utcnow()
        db_gift = await self.save(db_gift)
        await GiftCache.delete(code)
        return db_gift

    async def expire_old(self) -> int:
        result = await self.session.execute(
            select(Gift).where(
                and_(
                    Gift.status == GiftStatus.PENDING,
                    Gift.expires_at < datetime.utcnow(),
                )
            )
        )
        expired = list(result.scalars().all())
        for g in expired:
            g.status = GiftStatus.EXPIRED
            self.session.add(g)
            await GiftCache.delete(g.activation_code)
        await self.session.commit()
        return len(expired)

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.cache import UserCache, model_to_dict
from database.models.user import User, Referral
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_chat_id(self, chat_id: int) -> User | None:
        cached = await UserCache.get(chat_id)
        if cached:
            return User(**{k: v for k, v in cached.items() if k in User.__table__.columns.keys()})
        result = await self.session.execute(select(User).where(User.chat_id == chat_id))
        user = result.scalar_one_or_none()
        if user:
            await UserCache.set(chat_id, model_to_dict(user))
        return user

    async def get_by_ref_code(self, ref_code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.ref_code == ref_code))
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        chat_id: int,
        first_name: str | None = None,
        username: str | None = None,
        language_code: str = "ru",
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            chat_id=chat_id,
            first_name=first_name,
            username=username,
            language_code=language_code,
        )
        return await self.save(user)

    async def update_last_activity(self, user: User) -> None:
        user.last_activity = datetime.utcnow()
        self.session.add(user)
        await self.session.commit()
        await UserCache.delete(user.chat_id)

    async def update_balance(self, user: User, new_balance: float) -> User:
        user.balance_rub = new_balance
        user = await self.save(user)
        await UserCache.delete(user.chat_id)
        return user

    async def set_banned(self, user: User, banned: bool) -> User:
        user.is_banned = banned
        user = await self.save(user)
        await UserCache.delete(user.chat_id)
        return user

    async def set_blocked_bot(self, user: User, blocked: bool) -> User:
        user.blocked_bot = blocked
        user = await self.save(user)
        await UserCache.delete(user.chat_id)
        return user

    async def update_language(self, user: User, lang: str) -> User:
        user.language_code = lang
        user = await self.save(user)
        await UserCache.delete(user.chat_id)
        return user

    async def get_all_active(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_banned == False, User.blocked_bot == False)
        )
        return list(result.scalars().all())


class ReferralRepository(BaseRepository[Referral]):
    model = Referral

    async def get_by_referred_user_id(self, referred_user_id: int) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_user_id == referred_user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, referrer_user_id: int, referred_user_id: int) -> Referral:
        ref = Referral(referrer_user_id=referrer_user_id, referred_user_id=referred_user_id)
        return await self.save(ref)

    async def mark_reward_credited(self, referral: Referral) -> Referral:
        referral.reward_credited = True
        return await self.save(referral)

from decimal import Decimal

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from database.models.settings import ChannelSettings
from database.repositories import UserRepository, ReferralRepository, ChannelSettingsRepository
from config import logger


class InsufficientBalanceError(Exception):
    pass


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.referral_repo = ReferralRepository(session)
        self.channel_repo = ChannelSettingsRepository(session)

    async def register_or_get(
        self,
        telegram_id: int,
        chat_id: int,
        first_name: str | None = None,
        username: str | None = None,
        language_code: str = "ru",
    ) -> tuple[User, bool]:
        """Returns (user, is_new)."""
        user = await self.user_repo.get_by_chat_id(chat_id)
        if user is not None:
            return user, False
        user = await self.user_repo.create(
            telegram_id=telegram_id,
            chat_id=chat_id,
            first_name=first_name,
            username=username,
            language_code=language_code,
        )
        return user, True

    async def update_activity(self, user: User) -> None:
        await self.user_repo.update_last_activity(user)

    async def credit_balance(self, user: User, amount: float) -> User:
        new_balance = float(Decimal(str(user.balance_rub)) + Decimal(str(amount)))
        return await self.user_repo.update_balance(user, new_balance)

    async def debit_balance(self, user: User, amount: float) -> User:
        current = Decimal(str(user.balance_rub))
        to_debit = Decimal(str(amount))
        if current < to_debit:
            raise InsufficientBalanceError(
                f"Balance {current} is less than required {to_debit}"
            )
        new_balance = float(current - to_debit)
        return await self.user_repo.update_balance(user, new_balance)

    async def check_channel_membership(self, user: User, bot: Bot) -> bool:
        channel_settings: ChannelSettings | None = await self.channel_repo.get()
        if not channel_settings or not channel_settings.is_enabled:
            return True
        if not channel_settings.channel_id:
            return True
        try:
            member = await bot.get_chat_member(channel_settings.channel_id, user.telegram_id)
            return member.status not in ("left", "kicked", "banned")
        except (TelegramBadRequest, TelegramForbiddenError):
            return True  # if we can't check (e.g. bot not in channel), don't block

    async def ban(self, user: User) -> User:
        return await self.user_repo.set_banned(user, True)

    async def unban(self, user: User) -> User:
        return await self.user_repo.set_banned(user, False)

    async def set_blocked_bot(self, user: User, blocked: bool) -> User:
        return await self.user_repo.set_blocked_bot(user, blocked)

    async def update_language(self, user: User, lang: str) -> User:
        return await self.user_repo.update_language(user, lang)

    async def get_by_chat_id(self, chat_id: int) -> User | None:
        return await self.user_repo.get_by_chat_id(chat_id)

    async def get_all_active(self) -> list[User]:
        return await self.user_repo.get_all_active()

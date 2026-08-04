from sqlalchemy import select

from database.cache import BotSettingsCache, ReferralSettingsCache, ChannelSettingsCache, model_to_dict
from database.models.settings import BotSettings, ChannelSettings, ReferralSettings
from .base import BaseRepository


class BotSettingsRepository(BaseRepository[BotSettings]):
    model = BotSettings

    async def get(self) -> BotSettings | None:
        cached = await BotSettingsCache.get()
        if cached:
            return BotSettings(**{k: v for k, v in cached.items() if k in BotSettings.__table__.columns.keys()})
        result = await self.session.execute(select(BotSettings).where(BotSettings.id == 1))
        obj = result.scalar_one_or_none()
        if obj:
            await BotSettingsCache.set(model_to_dict(obj))
        return obj

    async def save_and_invalidate(self, obj: BotSettings) -> BotSettings:
        obj = await self.save(obj)
        await BotSettingsCache.delete()
        return obj


class ReferralSettingsRepository(BaseRepository[ReferralSettings]):
    model = ReferralSettings

    async def get(self) -> ReferralSettings | None:
        cached = await ReferralSettingsCache.get()
        if cached:
            return ReferralSettings(**{k: v for k, v in cached.items() if k in ReferralSettings.__table__.columns.keys()})
        result = await self.session.execute(select(ReferralSettings).where(ReferralSettings.id == 1))
        obj = result.scalar_one_or_none()
        if obj:
            await ReferralSettingsCache.set(model_to_dict(obj))
        return obj

    async def save_and_invalidate(self, obj: ReferralSettings) -> ReferralSettings:
        obj = await self.save(obj)
        await ReferralSettingsCache.delete()
        return obj


class ChannelSettingsRepository(BaseRepository[ChannelSettings]):
    model = ChannelSettings

    async def get(self) -> ChannelSettings | None:
        cached = await ChannelSettingsCache.get()
        if cached:
            return ChannelSettings(**{k: v for k, v in cached.items() if k in ChannelSettings.__table__.columns.keys()})
        result = await self.session.execute(select(ChannelSettings).where(ChannelSettings.id == 1))
        obj = result.scalar_one_or_none()
        if obj:
            await ChannelSettingsCache.set(model_to_dict(obj))
        return obj

    async def save_and_invalidate(self, obj: ChannelSettings) -> ChannelSettings:
        obj = await self.save(obj)
        await ChannelSettingsCache.delete()
        return obj

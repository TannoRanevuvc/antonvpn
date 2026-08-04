from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.cache import TariffCache, model_to_dict
from database.models.tariff import Tariff
from database.models.subscription import TariffType
from .base import BaseRepository


class TariffRepository(BaseRepository[Tariff]):
    model = Tariff

    async def get_active(self) -> list[Tariff]:
        cached = await TariffCache.get()
        if cached is not None:
            return [Tariff(**item) for item in cached]
        result = await self.session.execute(
            select(Tariff).where(Tariff.is_active == True).order_by(Tariff.sort_order, Tariff.id)
        )
        tariffs = list(result.scalars().all())
        await TariffCache.set([model_to_dict(t) for t in tariffs])
        return tariffs

    async def get_by_type(self, tariff_type: TariffType) -> list[Tariff]:
        all_active = await self.get_active()
        return [t for t in all_active if t.tariff_type == tariff_type]

    async def get_by_id_active(self, tariff_id: int) -> Tariff | None:
        all_active = await self.get_active()
        for t in all_active:
            if t.id == tariff_id:
                return t
        return None

    async def invalidate_cache(self) -> None:
        await TariffCache.delete()

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.subscription import TariffType
from database.models.tariff import Tariff
from database.repositories import TariffRepository


class TariffService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TariffRepository(session)

    async def list_active(self) -> list[Tariff]:
        return await self.repo.get_active()

    async def list_by_type(self, tariff_type: TariffType) -> list[Tariff]:
        return await self.repo.get_by_type(tariff_type)

    async def get_by_id(self, tariff_id: int) -> Tariff | None:
        return await self.repo.get_by_id_active(tariff_id)

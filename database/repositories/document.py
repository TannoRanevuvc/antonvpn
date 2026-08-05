from sqlalchemy import select

from database.models.document import LegalDocument
from .base import BaseRepository


class LegalDocumentRepository(BaseRepository[LegalDocument]):
    model = LegalDocument

    async def get_by_slug(self, slug: str) -> LegalDocument | None:
        result = await self.session.execute(
            select(LegalDocument).where(LegalDocument.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[LegalDocument]:
        result = await self.session.execute(select(LegalDocument).order_by(LegalDocument.id))
        return list(result.scalars().all())

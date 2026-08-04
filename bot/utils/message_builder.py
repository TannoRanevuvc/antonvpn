"""Load message text + optional media from DB (with Redis cache)."""
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import MessageTemplateRepository


async def build_payload_by_key(key: str, session: AsyncSession) -> dict:
    """Returns {'text': str, 'image_path': str|None}."""
    repo = MessageTemplateRepository(session)
    template = await repo.get_by_key(key)
    if template is None:
        return {"text": f"[{key}]", "image_path": None}
    return {"text": template.text, "image_path": template.image_path}

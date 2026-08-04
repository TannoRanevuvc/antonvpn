from sqlalchemy import select

from database.cache import MessageCache, model_to_dict
from database.models.message import MessageTemplate
from .base import BaseRepository


class MessageTemplateRepository(BaseRepository[MessageTemplate]):
    model = MessageTemplate

    async def get_by_key(self, key: str) -> MessageTemplate | None:
        cached = await MessageCache.get(key)
        if cached:
            return MessageTemplate(**{k: v for k, v in cached.items() if k in MessageTemplate.__table__.columns.keys()})
        result = await self.session.execute(select(MessageTemplate).where(MessageTemplate.key == key))
        template = result.scalar_one_or_none()
        if template:
            await MessageCache.set(key, model_to_dict(template))
        return template

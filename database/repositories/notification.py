from sqlalchemy import select

from database.models.notification import NotificationRule
from .base import BaseRepository


class NotificationRuleRepository(BaseRepository[NotificationRule]):
    model = NotificationRule

    async def get_active(self) -> list[NotificationRule]:
        result = await self.session.execute(
            select(NotificationRule)
            .where(NotificationRule.is_active == True)
            .order_by(NotificationRule.hours_before_expiry.desc())
        )
        return list(result.scalars().all())

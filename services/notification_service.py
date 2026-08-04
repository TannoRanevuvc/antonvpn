from sqlalchemy.ext.asyncio import AsyncSession

from database.models.notification import NotificationRule
from database.repositories import NotificationRuleRepository, MessageTemplateRepository
from config import logger


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rule_repo = NotificationRuleRepository(session)
        self.msg_repo = MessageTemplateRepository(session)

    async def get_active_rules(self) -> list[NotificationRule]:
        return await self.rule_repo.get_active()

    async def get_text_for_rule(self, rule: NotificationRule) -> str:
        template = await self.msg_repo.get_by_key(rule.message_template_key)
        if template:
            return template.text
        # Fallback texts
        fallbacks = {
            72: "⚠️ Ваша подписка заканчивается через 3 дня. Продлите, чтобы не потерять доступ.",
            24: "⚠️ Ваша подписка заканчивается через 1 день. Продлите сейчас!",
            1: "🔴 Ваша подписка заканчивается через 1 час!",
        }
        return fallbacks.get(rule.hours_before_expiry, "Ваша подписка скоро истечёт.")

from sqladmin import ModelView

from database.models.notification import NotificationRule


class NotificationRuleAdmin(ModelView, model=NotificationRule):
    name = "Правило уведомления"
    name_plural = "Правила уведомлений"
    icon = "fa-solid fa-bell"
    column_list = [NotificationRule.id, NotificationRule.label, NotificationRule.hours_before_expiry, NotificationRule.message_template_key, NotificationRule.is_active]
    form_columns = [NotificationRule.label, NotificationRule.hours_before_expiry, NotificationRule.message_template_key, NotificationRule.is_active]

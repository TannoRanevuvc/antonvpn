from sqladmin import ModelView

from database.models.message import MessageTemplate


class MessageTemplateAdmin(ModelView, model=MessageTemplate):
    name = "Шаблон сообщения"
    name_plural = "Шаблоны сообщений"
    icon = "fa-solid fa-message"
    column_list = [MessageTemplate.id, MessageTemplate.key, MessageTemplate.text]
    column_searchable_list = [MessageTemplate.key]
    form_columns = [MessageTemplate.key, MessageTemplate.text, MessageTemplate.image_path]

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import MessageCache
        await MessageCache.delete(model.key)

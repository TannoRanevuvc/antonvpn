import os

from sqladmin import ModelView
from wtforms import FileField

from database.models.document import LegalDocument


class LegalDocumentAdmin(ModelView, model=LegalDocument):
    name = "Документ"
    name_plural = "Юридические документы"
    icon = "fa-solid fa-file-contract"

    column_list = [LegalDocument.id, LegalDocument.slug, LegalDocument.title, LegalDocument.updated_at]
    column_searchable_list = [LegalDocument.slug, LegalDocument.title]

    form_columns = [
        LegalDocument.slug,
        LegalDocument.title,
        LegalDocument.html_content,
    ]

    form_args = {
        "html_content": {"render_kw": {"rows": 30, "style": "font-family:monospace;font-size:13px;"}},
        "slug": {"render_kw": {"placeholder": "privacy-policy"}},
    }

    async def scaffold_form(self, rules=None):
        base = await super().scaffold_form(rules)
        extra = {"file_upload": FileField("Загрузить HTML-файл (заменит содержимое)")}
        return type(base.__name__, (base,), extra)

    async def on_model_change(self, data, model, is_created, request) -> None:
        uploaded = data.pop("file_upload", None)
        if uploaded and getattr(uploaded, "filename", None):
            content = uploaded.file.read()
            try:
                data["html_content"] = content.decode("utf-8")
            except UnicodeDecodeError:
                data["html_content"] = content.decode("latin-1")

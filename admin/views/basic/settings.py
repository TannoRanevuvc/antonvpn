import os

import aiohttp
from sqladmin import ModelView
from wtforms import FileField

from config import settings as app_settings
from database.models.settings import BotSettings, ChannelSettings, ReferralSettings

OFERTA_DIR = "media/oferta"
os.makedirs(OFERTA_DIR, exist_ok=True)


async def _apply_bot_description(model: BotSettings) -> None:
    token = app_settings.TOKEN_BOT_TG
    base = f"https://api.telegram.org/bot{token}"
    proxy = app_settings.SOCKS5_PROXY_URL or None
    async with aiohttp.ClientSession() as session:
        if model.bot_description is not None:
            await session.post(
                f"{base}/setMyDescription",
                json={"description": model.bot_description, "language_code": "ru"},
                proxy=proxy,
            )
        if model.bot_short_description is not None:
            await session.post(
                f"{base}/setMyShortDescription",
                json={"short_description": model.bot_short_description, "language_code": "ru"},
                proxy=proxy,
            )


class BotSettingsAdmin(ModelView, model=BotSettings):
    name = "Настройки бота"
    name_plural = "Настройки бота"
    icon = "fa-solid fa-gear"
    column_list = [BotSettings.id, BotSettings.registration_enabled, BotSettings.trial_days, BotSettings.site_url, BotSettings.updated_at]
    form_columns = [
        BotSettings.registration_enabled,
        BotSettings.trial_days,
        BotSettings.trial_squad_uuid,
        BotSettings.default_squad_uuid,
        BotSettings.site_url,
        BotSettings.news_channel_url,
        BotSettings.support_url,
        BotSettings.bot_description,
        BotSettings.bot_short_description,
        BotSettings.oferta_file_path,
    ]
    form_include_pk = False
    can_create = False
    can_delete = False

    async def scaffold_form(self, rules=None):
        base = await super().scaffold_form(rules)
        extra = {"oferta_upload": FileField("Загрузить файл оферты (PDF/документ)")}
        return type(base.__name__, (base,), extra)

    async def on_model_change(self, data, model, is_created, request) -> None:
        oferta = data.pop("oferta_upload", None)
        if oferta and getattr(oferta, "filename", None):
            ext = os.path.splitext(oferta.filename)[1] or ".pdf"
            dest = os.path.join(OFERTA_DIR, f"oferta{ext}")
            with open(dest, "wb") as f:
                f.write(oferta.file.read())
            data["oferta_file_path"] = dest

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import BotSettingsCache
        await BotSettingsCache.delete()
        await _apply_bot_description(model)


class ReferralSettingsAdmin(ModelView, model=ReferralSettings):
    name = "Реферальная программа"
    name_plural = "Реферальная программа"
    icon = "fa-solid fa-handshake"
    column_list = [
        ReferralSettings.id,
        ReferralSettings.is_enabled,
        ReferralSettings.level1_percent,
        ReferralSettings.level2_percent,
        ReferralSettings.max_paid_topups,
    ]
    form_columns = [
        ReferralSettings.is_enabled,
        ReferralSettings.level1_percent,
        ReferralSettings.level2_percent,
        ReferralSettings.max_paid_topups,
    ]
    column_labels = {
        "level1_percent": "% за 1-й уровень",
        "level2_percent": "% за 2-й уровень",
        "max_paid_topups": "Макс. пополнений для начисления",
    }
    can_create = False
    can_delete = False

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import ReferralSettingsCache
        await ReferralSettingsCache.delete()


class ChannelSettingsAdmin(ModelView, model=ChannelSettings):
    name = "Настройки канала"
    name_plural = "Настройки канала"
    icon = "fa-solid fa-satellite-dish"
    column_list = [ChannelSettings.id, ChannelSettings.is_enabled, ChannelSettings.channel_id, ChannelSettings.channel_url]
    form_columns = [ChannelSettings.is_enabled, ChannelSettings.channel_id, ChannelSettings.channel_url]
    can_create = False
    can_delete = False

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import ChannelSettingsCache
        await ChannelSettingsCache.delete()

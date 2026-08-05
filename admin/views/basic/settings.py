import os

import aiohttp
from sqladmin import ModelView
from wtforms import FileField

from config import settings as app_settings
from database.models.settings import BotSettings, ChannelSettings, ReferralSettings

OFERTA_DIR = "media/oferta"
os.makedirs(OFERTA_DIR, exist_ok=True)


async def _apply_bot_description(model: BotSettings) -> None:
    """Push description and short_description to Telegram Bot API."""
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
        BotSettings.site_url,
        BotSettings.news_channel_url,
        BotSettings.support_url,
        BotSettings.bot_description,
        BotSettings.bot_short_description,
        BotSettings.oferta_file_path,
    ]
    form_extra_fields = {"oferta_upload": FileField("Загрузить файл оферты (PDF/документ)")}
    form_include_pk = False
    can_create = False
    can_delete = False

    async def on_model_change(self, data, model, is_created, request) -> None:
        upload = data.pop("oferta_upload", None)
        if upload and getattr(upload, "filename", None):
            ext = os.path.splitext(upload.filename)[1] or ".pdf"
            dest = os.path.join(OFERTA_DIR, f"oferta{ext}")
            contents = upload.file.read()
            with open(dest, "wb") as f:
                f.write(contents)
            data["oferta_file_path"] = dest

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import BotSettingsCache
        await BotSettingsCache.delete()
        await _apply_bot_description(model)


class ReferralSettingsAdmin(ModelView, model=ReferralSettings):
    name = "Реферальная программа"
    name_plural = "Реферальная программа"
    icon = "fa-solid fa-handshake"
    column_list = [ReferralSettings.id, ReferralSettings.is_enabled, ReferralSettings.reward_type, ReferralSettings.reward_amount, ReferralSettings.max_rewards_per_referrer]
    form_columns = [ReferralSettings.is_enabled, ReferralSettings.reward_type, ReferralSettings.reward_amount, ReferralSettings.max_rewards_per_referrer]
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

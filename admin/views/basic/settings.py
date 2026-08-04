from sqladmin import ModelView

from database.models.settings import BotSettings, ChannelSettings, ReferralSettings


class BotSettingsAdmin(ModelView, model=BotSettings):
    name = "Настройки бота"
    name_plural = "Настройки бота"
    icon = "fa-solid fa-gear"
    column_list = [BotSettings.id, BotSettings.registration_enabled, BotSettings.trial_days, BotSettings.site_url, BotSettings.updated_at]
    form_columns = [BotSettings.registration_enabled, BotSettings.trial_days, BotSettings.site_url, BotSettings.news_channel_url, BotSettings.support_url]
    can_create = False
    can_delete = False

    async def after_model_change(self, data, model, is_created, request) -> None:
        from database.cache import BotSettingsCache
        await BotSettingsCache.delete()


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

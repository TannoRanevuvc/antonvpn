from sqladmin import ModelView

from database.models.subscription import Device, Subscription


class SubscriptionAdmin(ModelView, model=Subscription):
    name = "Подписка"
    name_plural = "Подписки"
    icon = "fa-solid fa-key"
    column_list = [
        Subscription.id, Subscription.user_id, Subscription.remna_username,
        Subscription.remna_status, Subscription.tariff_type, Subscription.expires_at,
        Subscription.auto_renewal, Subscription.created_at,
    ]
    column_searchable_list = [Subscription.remna_username]
    column_sortable_list = [Subscription.expires_at, Subscription.created_at]
    column_default_sort = [(Subscription.created_at, True)]
    form_columns = [
        Subscription.display_name, Subscription.remna_status, Subscription.expires_at,
        Subscription.auto_renewal,
    ]
    can_create = False


class DeviceAdmin(ModelView, model=Device):
    name = "Устройство"
    name_plural = "Устройства"
    icon = "fa-solid fa-mobile"
    column_list = [Device.id, Device.subscription_id, Device.model, Device.os, Device.last_seen, Device.synced_at]
    can_create = False
    can_edit = False

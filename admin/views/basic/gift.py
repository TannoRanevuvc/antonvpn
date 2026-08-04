from sqladmin import ModelView

from database.models.gift import Gift


class GiftAdmin(ModelView, model=Gift):
    name = "Подарок"
    name_plural = "Подарки"
    icon = "fa-solid fa-gift"
    column_list = [Gift.id, Gift.sender_user_id, Gift.recipient_user_id, Gift.tariff_id, Gift.amount_rub, Gift.status, Gift.created_at, Gift.expires_at]
    column_sortable_list = [Gift.created_at]
    form_columns = [Gift.status]
    can_create = False

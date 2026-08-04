from sqladmin import ModelView

from database.models.payment import Payment, TopUp


class TopUpAdmin(ModelView, model=TopUp):
    name = "Пополнение"
    name_plural = "Пополнения"
    icon = "fa-solid fa-wallet"
    column_list = [TopUp.id, TopUp.user_id, TopUp.chat_id, TopUp.amount_rub, TopUp.status, TopUp.created_at, TopUp.paid_at]
    column_sortable_list = [TopUp.created_at]
    column_default_sort = [(TopUp.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class PaymentAdmin(ModelView, model=Payment):
    name = "Платёж"
    name_plural = "Платежи"
    icon = "fa-solid fa-receipt"
    column_list = [Payment.id, Payment.user_id, Payment.amount_rub, Payment.status, Payment.is_renewal, Payment.created_at]
    column_sortable_list = [Payment.created_at]
    column_default_sort = [(Payment.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False

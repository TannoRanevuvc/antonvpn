from sqladmin import ModelView

from database.models.payment import Payment, TopUp
from database.models.referral_reward import ReferralReward


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


class ReferralRewardAdmin(ModelView, model=ReferralReward):
    name = "Реф. начисление"
    name_plural = "Реф. начисления"
    icon = "fa-solid fa-coins"
    column_list = [
        ReferralReward.id,
        ReferralReward.beneficiary_id,
        ReferralReward.payer_id,
        ReferralReward.level,
        ReferralReward.amount_rub,
        ReferralReward.topup_id,
        ReferralReward.created_at,
    ]
    column_sortable_list = [ReferralReward.created_at]
    column_default_sort = [(ReferralReward.created_at, True)]
    column_labels = {
        "beneficiary_id": "Получатель (ID)",
        "payer_id": "Плательщик (ID)",
        "level": "Уровень",
        "amount_rub": "Сумма ₽",
        "topup_id": "Пополнение",
    }
    can_create = False
    can_edit = False
    can_delete = False

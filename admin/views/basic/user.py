from sqladmin import ModelView

from database.models.user import Referral, User


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"
    column_list = [User.id, User.telegram_id, User.first_name, User.username, User.balance_rub, User.is_banned, User.created_at]
    column_searchable_list = [User.telegram_id, User.username, User.ref_code]
    column_sortable_list = [User.created_at, User.last_activity, User.balance_rub]
    column_default_sort = [(User.created_at, True)]
    form_columns = [User.first_name, User.username, User.language_code, User.balance_rub, User.is_banned, User.blocked_bot]
    can_create = False
    can_delete = False


class ReferralAdmin(ModelView, model=Referral):
    name = "Реферал"
    name_plural = "Рефералы"
    icon = "fa-solid fa-user-group"
    column_list = [Referral.id, Referral.referrer_user_id, Referral.referred_user_id, Referral.reward_credited, Referral.created_at]
    can_create = False
    can_edit = False
    can_delete = False

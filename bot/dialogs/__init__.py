from .cabinet import create_cabinet_dialog
from .consent import create_consent_dialog
from .subscriptions import create_subscriptions_dialog
from .tariffs import create_tariffs_dialog
from .payments import create_payments_dialog
from .gifts import create_gifts_dialog, create_gift_activate_dialog
from .referral import create_referral_dialog
from .notifications import create_notifications_dialog
from .channel_gate import create_channel_gate_dialog


def get_all_dialogs():
    return [
        create_consent_dialog(),
        create_cabinet_dialog(),
        create_subscriptions_dialog(),
        create_tariffs_dialog(),
        create_payments_dialog(),
        create_gifts_dialog(),
        create_gift_activate_dialog(),
        create_referral_dialog(),
        create_notifications_dialog(),
        create_channel_gate_dialog(),
    ]

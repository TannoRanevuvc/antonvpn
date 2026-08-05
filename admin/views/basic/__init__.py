from .user import UserAdmin, ReferralAdmin
from .subscription import SubscriptionAdmin, DeviceAdmin
from .tariff import TariffAdmin
from .payment import TopUpAdmin, PaymentAdmin, ReferralRewardAdmin
from .gift import GiftAdmin
from .message import MessageTemplateAdmin
from .notification import NotificationRuleAdmin
from .settings import BotSettingsAdmin, ReferralSettingsAdmin, ChannelSettingsAdmin
from .document import LegalDocumentAdmin

__all__ = [
    "UserAdmin", "ReferralAdmin",
    "SubscriptionAdmin", "DeviceAdmin",
    "TariffAdmin",
    "TopUpAdmin", "PaymentAdmin", "ReferralRewardAdmin",
    "GiftAdmin",
    "MessageTemplateAdmin",
    "NotificationRuleAdmin",
    "BotSettingsAdmin", "ReferralSettingsAdmin", "ChannelSettingsAdmin",
    "LegalDocumentAdmin",
]

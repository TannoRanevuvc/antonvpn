from aiogram.fsm.state import State, StatesGroup


class CabinetSG(StatesGroup):
    MAIN = State()


class SubscriptionsSG(StatesGroup):
    LIST = State()
    DETAIL = State()
    DEVICES = State()
    RENAME = State()


class TariffsSG(StatesGroup):
    TYPE_SELECT = State()
    LIST = State()
    CONFIRM = State()


class PaymentsSG(StatesGroup):
    TOPUP_AMOUNT = State()
    CONFIRM = State()
    SUCCESS = State()


class GiftsSG(StatesGroup):
    TARIFF_SELECT = State()
    CONFIRM = State()
    SENT = State()


class GiftActivateSG(StatesGroup):
    ACTIVATE = State()
    SUCCESS = State()


class ReferralSG(StatesGroup):
    INFO = State()


class NotifySG(StatesGroup):
    EXPIRY_3D = State()
    EXPIRY_1D = State()
    EXPIRY_1H = State()
    EXPIRED = State()


class ChannelGateSG(StatesGroup):
    CHECK = State()


class OfertaSG(StatesGroup):
    VIEW = State()

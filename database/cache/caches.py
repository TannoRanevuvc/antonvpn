from .base import CacheService

_TTL_USER = 600       # 10 min
_TTL_SUB = 300        # 5 min
_TTL_TARIFF = 600     # 10 min
_TTL_MSG = 600        # 10 min
_TTL_SETTINGS = 1800  # 30 min
_TTL_GIFT = 1800      # 30 min
_TTL_DASHBOARD = 60   # 1 min


class UserCache:
    @staticmethod
    def _key(chat_id: int) -> str:
        return f"anton:user:{chat_id}"

    @staticmethod
    async def get(chat_id: int) -> dict | None:
        return await CacheService.get(UserCache._key(chat_id))

    @staticmethod
    async def set(chat_id: int, data: dict) -> None:
        await CacheService.set(UserCache._key(chat_id), data, expire=_TTL_USER)

    @staticmethod
    async def delete(chat_id: int) -> None:
        await CacheService.delete(UserCache._key(chat_id))


class SubscriptionCache:
    @staticmethod
    def _key(user_id: int) -> str:
        return f"anton:sub:user:{user_id}"

    @staticmethod
    async def get(user_id: int) -> dict | None:
        return await CacheService.get(SubscriptionCache._key(user_id))

    @staticmethod
    async def set(user_id: int, data: dict) -> None:
        await CacheService.set(SubscriptionCache._key(user_id), data, expire=_TTL_SUB)

    @staticmethod
    async def delete(user_id: int) -> None:
        await CacheService.delete(SubscriptionCache._key(user_id))


class TariffCache:
    _KEY = "anton:tariffs:active"

    @staticmethod
    async def get() -> list | None:
        raw = await CacheService.get(TariffCache._KEY)
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict) and "items" in raw:
            return raw["items"]
        return None

    @staticmethod
    async def set(items: list) -> None:
        await CacheService.set(TariffCache._KEY, {"items": items}, expire=_TTL_TARIFF)

    @staticmethod
    async def delete() -> None:
        await CacheService.delete(TariffCache._KEY)


class MessageCache:
    @staticmethod
    def _key(msg_key: str) -> str:
        return f"anton:msg:{msg_key}"

    @staticmethod
    async def get(msg_key: str) -> dict | None:
        return await CacheService.get(MessageCache._key(msg_key))

    @staticmethod
    async def set(msg_key: str, data: dict) -> None:
        await CacheService.set(MessageCache._key(msg_key), data, expire=_TTL_MSG)

    @staticmethod
    async def delete(msg_key: str) -> None:
        await CacheService.delete(MessageCache._key(msg_key))


class BotSettingsCache:
    _KEY = "anton:settings:bot"

    @staticmethod
    async def get() -> dict | None:
        return await CacheService.get(BotSettingsCache._KEY)

    @staticmethod
    async def set(data: dict) -> None:
        await CacheService.set(BotSettingsCache._KEY, data, expire=_TTL_SETTINGS)

    @staticmethod
    async def delete() -> None:
        await CacheService.delete(BotSettingsCache._KEY)


class ReferralSettingsCache:
    _KEY = "anton:settings:referral"

    @staticmethod
    async def get() -> dict | None:
        return await CacheService.get(ReferralSettingsCache._KEY)

    @staticmethod
    async def set(data: dict) -> None:
        await CacheService.set(ReferralSettingsCache._KEY, data, expire=_TTL_SETTINGS)

    @staticmethod
    async def delete() -> None:
        await CacheService.delete(ReferralSettingsCache._KEY)


class ChannelSettingsCache:
    _KEY = "anton:settings:channel"

    @staticmethod
    async def get() -> dict | None:
        return await CacheService.get(ChannelSettingsCache._KEY)

    @staticmethod
    async def set(data: dict) -> None:
        await CacheService.set(ChannelSettingsCache._KEY, data, expire=_TTL_SETTINGS)

    @staticmethod
    async def delete() -> None:
        await CacheService.delete(ChannelSettingsCache._KEY)


class GiftCache:
    @staticmethod
    def _key(code: str) -> str:
        return f"anton:gift:code:{code}"

    @staticmethod
    async def get(code: str) -> dict | None:
        return await CacheService.get(GiftCache._key(code))

    @staticmethod
    async def set(code: str, data: dict) -> None:
        await CacheService.set(GiftCache._key(code), data, expire=_TTL_GIFT)

    @staticmethod
    async def delete(code: str) -> None:
        await CacheService.delete(GiftCache._key(code))


class DashboardCache:
    _KEY = "anton:sqladmin:dashboard"

    @staticmethod
    async def get() -> dict | None:
        return await CacheService.get(DashboardCache._KEY)

    @staticmethod
    async def set(data: dict) -> None:
        await CacheService.set(DashboardCache._KEY, data, expire=_TTL_DASHBOARD)

    @staticmethod
    async def delete() -> None:
        await CacheService.delete(DashboardCache._KEY)

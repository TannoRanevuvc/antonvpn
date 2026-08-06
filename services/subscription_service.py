"""Business logic for VPN subscription lifecycle."""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.subscription import Device, RemnaStatus, Subscription, TariffType
from database.models.settings import BotSettings
from database.models.user import User
from database.repositories import (
    DeviceRepository,
    PaymentRepository,
    SubscriptionRepository,
    TariffRepository,
)
from .remnawave_service import RemnawaveService
from .user_service import InsufficientBalanceError, UserService
from config import logger, settings as app_settings


class TrialNotAvailableError(Exception):
    pass


def _make_remna_username(chat_id: int) -> str:
    short = uuid.uuid4().hex[:8]
    return f"u{chat_id}_{short}"


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.sub_repo = SubscriptionRepository(session)
        self.device_repo = DeviceRepository(session)
        self.tariff_repo = TariffRepository(session)
        self.payment_repo = PaymentRepository(session)
        self.user_service = UserService(session)
        self.remna = RemnawaveService()

    async def list_for_user(self, user_id: int) -> list[Subscription]:
        return await self.sub_repo.get_by_user_id(user_id)

    async def get_subscription(self, sub_id: int, user_id: int) -> Subscription | None:
        return await self.sub_repo.get_by_id_and_user(sub_id, user_id)

    def _unwrap_remna(self, remna_data: dict) -> dict:
        if isinstance(remna_data.get("response"), dict):
            return remna_data["response"]
        return remna_data

    def _extract_remna_fields(self, remna_data: dict) -> tuple[str, str | None, str | None]:
        from urllib.parse import urlparse
        payload = self._unwrap_remna(remna_data)
        remna_uuid = payload.get("uuid") or payload.get("vlessUuid") or ""
        short_uuid = payload.get("shortUuid")
        raw_url = payload.get("subscriptionUrl")
        if raw_url:
            # Remnawave returns /api/sub/{uuid}; sub-page serves at /sub/{uuid}
            sub_url = raw_url.replace("/api/sub/", "/sub/")
        elif short_uuid:
            parsed = urlparse(app_settings.ADMIN_PUBLIC_BASE_URL)
            public_base = f"{parsed.scheme}://{parsed.netloc}"
            sub_url = f"{public_base}/sub/{short_uuid}"
        else:
            sub_url = None
        return remna_uuid, short_uuid, sub_url

    async def create_trial(self, user: User, bot_settings: BotSettings) -> Subscription:
        if not bot_settings or not bot_settings.trial_days:
            raise TrialNotAvailableError("Trial is not configured")

        already_used = await self.sub_repo.has_trial_subscription(user.id)
        if already_used:
            raise TrialNotAvailableError("Trial already used")

        squad_uuid = bot_settings.trial_squad_uuid
        expires_at = datetime.utcnow() + timedelta(days=bot_settings.trial_days)
        remna_username = _make_remna_username(user.chat_id)

        sub = await self.sub_repo.create(
            user_id=user.id,
            remna_username=remna_username,
            tariff_type=TariffType.VPN,
            squad_uuid=squad_uuid,
            max_devices=1,
            is_trial=True,
        )

        try:
            remna_data = await self.remna.create_user(
                username=remna_username,
                expires_at=expires_at,
                squad_uuid=squad_uuid,
            )
            remna_uuid, short_uuid, sub_url = self._extract_remna_fields(remna_data)
            sub = await self.sub_repo.update_remna_data(sub, remna_uuid, short_uuid, sub_url, expires_at)
        except Exception as exc:
            logger.error("Remnawave create_user failed for trial sub %s: %s", sub.id, exc)

        return sub

    async def create(self, user: User, tariff_id: int, bot_settings: BotSettings | None = None) -> Subscription:
        tariff = await self.tariff_repo.get_by_id_active(tariff_id)
        if tariff is None:
            raise ValueError(f"Tariff {tariff_id} not found or inactive")

        # All paid subscriptions go to the default squad
        squad_uuid = (bot_settings.default_squad_uuid if bot_settings else None) or tariff.squad_uuid

        # Debit balance
        user = await self.user_service.debit_balance(user, float(tariff.price_rub))

        expires_at = datetime.utcnow() + timedelta(days=tariff.duration_days)
        remna_username = _make_remna_username(user.chat_id)

        # Create local record first (DB-first)
        sub = await self.sub_repo.create(
            user_id=user.id,
            remna_username=remna_username,
            tariff_type=TariffType(tariff.tariff_type),
            tariff_id=tariff.id,
            squad_uuid=squad_uuid,
            max_devices=tariff.max_devices,
        )

        # Create payment ledger record
        payment = await self.payment_repo.create(
            user_id=user.id,
            amount_rub=float(tariff.price_rub),
            subscription_id=sub.id,
            tariff_id=tariff.id,
        )

        # Sync with Remnawave panel (best-effort — sub is already persisted)
        try:
            remna_data = await self.remna.create_user(
                username=remna_username,
                expires_at=expires_at,
                squad_uuid=squad_uuid,
            )
            remna_uuid, short_uuid, sub_url = self._extract_remna_fields(remna_data)
            sub = await self.sub_repo.update_remna_data(sub, remna_uuid, short_uuid, sub_url, expires_at)
            await self.payment_repo.mark_completed(payment)
        except Exception as exc:
            logger.error("Remnawave create_user failed for sub %s: %s", sub.id, exc)
            await self.payment_repo.mark_failed(payment, reason=str(exc))

        return sub

    async def renew(self, sub: Subscription, user: User, tariff_id: int | None = None) -> Subscription:
        tid = tariff_id or sub.tariff_id
        if tid is None:
            raise ValueError("No tariff for renewal")

        tariff = await self.tariff_repo.get_by_id_active(tid)
        if tariff is None:
            raise ValueError(f"Tariff {tid} not found")

        user = await self.user_service.debit_balance(user, float(tariff.price_rub))

        sub_expires = sub.expires_at
        if isinstance(sub_expires, str):
            sub_expires = datetime.fromisoformat(sub_expires)
        base = sub_expires if sub_expires and sub_expires > datetime.utcnow() else datetime.utcnow()
        new_expiry = base + timedelta(days=tariff.duration_days)

        payment = await self.payment_repo.create(
            user_id=user.id,
            amount_rub=float(tariff.price_rub),
            subscription_id=sub.id,
            tariff_id=tariff.id,
            is_renewal=True,
        )

        sub = await self.sub_repo.update_expiry(sub, new_expiry)

        try:
            if sub.remna_uuid:
                await self.remna.update_user(sub.remna_uuid, status="ACTIVE", expires_at=new_expiry)
            await self.payment_repo.mark_completed(payment)
        except Exception as exc:
            logger.error("Remnawave update failed on renewal for sub %s: %s", sub.id, exc)
            await self.payment_repo.mark_failed(payment, reason=str(exc))

        return sub

    async def rename(self, sub: Subscription, user_id: int, new_name: str) -> Subscription:
        if sub.user_id != user_id:
            raise PermissionError("Not your subscription")
        return await self.sub_repo.rename(sub, new_name)

    async def toggle_auto_renewal(self, sub: Subscription, user_id: int) -> Subscription:
        if sub.user_id != user_id:
            raise PermissionError("Not your subscription")
        return await self.sub_repo.toggle_auto_renewal(sub)

    async def sync_devices_from_panel(self, sub: Subscription) -> list[Device]:
        if not sub.remna_uuid:
            return []
        raw_devices = await self.remna.list_devices(sub.remna_uuid)
        devices: list[Device] = []
        for rd in raw_devices:
            device_data = {
                "remna_device_id": str(rd.get("id", "")),
                "model": rd.get("model"),
                "os": rd.get("os"),
                "os_version": rd.get("osVersion"),
                "client_version": rd.get("clientVersion"),
                "last_seen": rd.get("lastSeen"),
            }
            if not device_data["remna_device_id"]:
                continue
            dev = await self.device_repo.upsert(sub.id, device_data)
            devices.append(dev)
        return devices

    async def delete_device(self, sub: Subscription, user_id: int, remna_device_id: str) -> bool:
        if sub.user_id != user_id:
            raise PermissionError("Not your subscription")
        if sub.remna_uuid:
            await self.remna.delete_device(sub.remna_uuid, remna_device_id)
        return await self.device_repo.delete_by_remna_id(remna_device_id)

    async def get_expiring_without_flag(self, hours_before: int) -> list[Subscription]:
        return await self.sub_repo.get_expiring_without_flag(hours_before)

    async def get_just_expired(self) -> list[Subscription]:
        return await self.sub_repo.get_just_expired()

    async def get_due_for_auto_renewal(self) -> list[Subscription]:
        return await self.sub_repo.get_due_for_auto_renewal()

    async def mark_expired(self, sub: Subscription) -> Subscription:
        if sub.remna_uuid:
            await self.remna.disable_user(sub.remna_uuid)
        return await self.sub_repo.mark_expired(sub)

    async def mark_notify_flag(self, sub: Subscription, hours_before: int) -> Subscription:
        return await self.sub_repo.mark_notify_flag(sub, hours_before)

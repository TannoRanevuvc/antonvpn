"""Business logic for VPN subscription lifecycle."""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.subscription import Device, RemnaStatus, Subscription, TariffType
from database.models.user import User
from database.repositories import (
    DeviceRepository,
    PaymentRepository,
    SubscriptionRepository,
    TariffRepository,
)
from .remnawave_service import RemnawaveService
from .user_service import InsufficientBalanceError, UserService
from config import logger


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

    async def create(self, user: User, tariff_id: int) -> Subscription:
        tariff = await self.tariff_repo.get_by_id_active(tariff_id)
        if tariff is None:
            raise ValueError(f"Tariff {tariff_id} not found or inactive")

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
            squad_uuid=tariff.squad_uuid,
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
                squad_uuid=tariff.squad_uuid,
            )
            # Remnawave wraps data in a "response" key
            remna_payload = remna_data.get("response") if isinstance(remna_data.get("response"), dict) else remna_data
            remna_uuid = remna_payload.get("uuid", "")
            short_uuid = remna_payload.get("shortUuid")
            sub_url = remna_payload.get("subscriptionUrl") or (
                f"{__import__('config').settings.REMNAWAVE_PANEL_URL}/api/sub/{short_uuid}"
                if short_uuid else None
            )
            sub = await self.sub_repo.update_remna_data(sub, remna_uuid, short_uuid, sub_url, expires_at)
            await self.payment_repo.mark_completed(payment)
        except Exception as exc:
            logger.error("Remnawave create_user failed for sub %s: %s", sub.id, exc)
            await self.payment_repo.mark_failed(payment, reason=str(exc))
            # Don't roll back — sub is created, user was debited; will retry on next check

        return sub

    async def renew(self, sub: Subscription, user: User, tariff_id: int | None = None) -> Subscription:
        tid = tariff_id or sub.tariff_id
        if tid is None:
            raise ValueError("No tariff for renewal")

        tariff = await self.tariff_repo.get_by_id_active(tid)
        if tariff is None:
            raise ValueError(f"Tariff {tid} not found")

        user = await self.user_service.debit_balance(user, float(tariff.price_rub))

        base = sub.expires_at if sub.expires_at and sub.expires_at > datetime.utcnow() else datetime.utcnow()
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

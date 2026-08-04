from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.cache import SubscriptionCache, model_to_dict
from database.models.subscription import Device, RemnaStatus, Subscription
from .base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    async def get_by_user_id(self, user_id: int) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, sub_id: int, user_id: int) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.id == sub_id,
                Subscription.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_remna_username(self, remna_username: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(Subscription.remna_username == remna_username)
        )
        return result.scalar_one_or_none()

    async def get_expiring_without_flag(
        self, hours_before: int, window_hours: float = 0.5
    ) -> list[Subscription]:
        now = datetime.utcnow()
        target_time = now + timedelta(hours=hours_before)
        low = target_time - timedelta(hours=window_hours)
        high = target_time + timedelta(hours=window_hours)

        flag_col = {
            72: Subscription.sub_remind_3d_sent,
            24: Subscription.sub_remind_1d_sent,
            1: Subscription.sub_remind_1h_sent,
        }.get(hours_before)

        if flag_col is None:
            return []

        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.expires_at >= low,
                    Subscription.expires_at <= high,
                    flag_col == False,
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                )
            )
        )
        return list(result.scalars().all())

    async def get_just_expired(self) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.expires_at < datetime.utcnow(),
                    Subscription.sub_expired_sent == False,
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                )
            )
        )
        return list(result.scalars().all())

    async def get_due_for_auto_renewal(self) -> list[Subscription]:
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.auto_renewal == True,
                    Subscription.expires_at >= now - timedelta(hours=1),
                    Subscription.expires_at <= now + timedelta(hours=1),
                    Subscription.remna_status == RemnaStatus.ACTIVE,
                )
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        remna_username: str,
        tariff_type,
        tariff_id: int | None = None,
        squad_uuid: str | None = None,
        max_devices: int = 1,
    ) -> Subscription:
        sub = Subscription(
            user_id=user_id,
            tariff_id=tariff_id,
            remna_username=remna_username,
            tariff_type=tariff_type,
            squad_uuid=squad_uuid,
            max_devices=max_devices,
        )
        sub = await self.save(sub)
        await SubscriptionCache.delete(user_id)
        return sub

    async def update_remna_data(
        self,
        sub: Subscription,
        remna_uuid: str,
        remna_short_uuid: str | None,
        remna_sub_url: str | None,
        expires_at: datetime | None = None,
    ) -> Subscription:
        sub.remna_uuid = remna_uuid
        sub.remna_short_uuid = remna_short_uuid
        sub.remna_sub_url = remna_sub_url
        if expires_at:
            sub.expires_at = expires_at
            sub.started_at = datetime.utcnow()
        sub = await self.save(sub)
        await SubscriptionCache.delete(sub.user_id)
        return sub

    async def update_expiry(self, sub: Subscription, new_expiry: datetime) -> Subscription:
        sub.expires_at = new_expiry
        sub.sub_remind_3d_sent = False
        sub.sub_remind_1d_sent = False
        sub.sub_remind_1h_sent = False
        sub.sub_expired_sent = False
        sub.remna_status = RemnaStatus.ACTIVE
        sub = await self.save(sub)
        await SubscriptionCache.delete(sub.user_id)
        return sub

    async def update_status(self, sub: Subscription, status: RemnaStatus) -> Subscription:
        sub.remna_status = status
        sub = await self.save(sub)
        await SubscriptionCache.delete(sub.user_id)
        return sub

    async def mark_expired(self, sub: Subscription) -> Subscription:
        sub.remna_status = RemnaStatus.DISABLED
        sub.sub_expired_sent = True
        sub = await self.save(sub)
        await SubscriptionCache.delete(sub.user_id)
        return sub

    async def mark_notify_flag(self, sub: Subscription, hours_before: int) -> Subscription:
        if hours_before == 72:
            sub.sub_remind_3d_sent = True
        elif hours_before == 24:
            sub.sub_remind_1d_sent = True
        elif hours_before == 1:
            sub.sub_remind_1h_sent = True
        return await self.save(sub)

    async def rename(self, sub: Subscription, new_name: str) -> Subscription:
        sub.display_name = new_name
        sub = await self.save(sub)
        await SubscriptionCache.delete(sub.user_id)
        return sub

    async def toggle_auto_renewal(self, sub: Subscription) -> Subscription:
        sub.auto_renewal = not sub.auto_renewal
        sub = await self.save(sub)
        await SubscriptionCache.delete(sub.user_id)
        return sub


class DeviceRepository(BaseRepository[Device]):
    model = Device

    async def list_by_subscription(self, subscription_id: int) -> list[Device]:
        result = await self.session.execute(
            select(Device).where(Device.subscription_id == subscription_id).order_by(Device.last_seen.desc())
        )
        return list(result.scalars().all())

    async def get_by_remna_device_id(self, remna_device_id: str) -> Device | None:
        result = await self.session.execute(
            select(Device).where(Device.remna_device_id == remna_device_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, subscription_id: int, device_data: dict) -> Device:
        device = await self.get_by_remna_device_id(device_data["remna_device_id"])
        if device is None:
            device = Device(subscription_id=subscription_id, **device_data)
        else:
            for k, v in device_data.items():
                setattr(device, k, v)
            device.synced_at = datetime.utcnow()
        return await self.save(device)

    async def delete_by_remna_id(self, remna_device_id: str) -> bool:
        device = await self.get_by_remna_device_id(remna_device_id)
        if device is None:
            return False
        await self.delete(device)
        return True

    async def delete_all_for_subscription(self, subscription_id: int) -> None:
        devices = await self.list_by_subscription(subscription_id)
        for d in devices:
            await self.delete(d)

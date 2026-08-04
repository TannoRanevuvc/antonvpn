from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.gift import Gift
from database.models.user import User
from database.repositories import GiftRepository, TariffRepository, UserRepository
from .user_service import UserService
from .subscription_service import SubscriptionService
from .referral_service import ReferralService
from config import logger


class GiftError(Exception):
    pass


class GiftService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.gift_repo = GiftRepository(session)
        self.tariff_repo = TariffRepository(session)
        self.user_service = UserService(session)
        self.sub_service = SubscriptionService(session)
        self.referral_service = ReferralService(session)

    async def create_gift(self, sender: User, tariff_id: int) -> Gift:
        tariff = await self.tariff_repo.get_by_id_active(tariff_id)
        if tariff is None:
            raise GiftError(f"Tariff {tariff_id} not found")

        await self.user_service.debit_balance(sender, float(tariff.price_rub))
        gift = await self.gift_repo.create(
            sender_user_id=sender.id,
            tariff_id=tariff_id,
            amount_rub=float(tariff.price_rub),
        )
        return gift

    async def activate_gift(self, code: str, recipient: User) -> Gift:
        gift = await self.gift_repo.get_by_code(code)
        if gift is None:
            raise GiftError("Gift not found")
        if gift.status != "pending":
            raise GiftError(f"Gift is already {gift.status}")
        if gift.expires_at and gift.expires_at < datetime.utcnow():
            raise GiftError("Gift has expired")
        if gift.sender_user_id == recipient.id:
            raise GiftError("Cannot activate your own gift")

        # Create subscription for recipient
        tariff = await self.tariff_repo.get_by_id_active(gift.tariff_id)
        if tariff is None:
            raise GiftError("Gift tariff no longer available")

        # We bypass balance check — gift was already paid by sender
        from datetime import timedelta
        from database.models.subscription import TariffType
        from database.repositories import SubscriptionRepository, PaymentRepository
        from services.remnawave_service import RemnawaveService
        from services.subscription_service import _make_remna_username

        sub_repo = SubscriptionRepository(self.session)
        payment_repo = PaymentRepository(self.session)
        remna = RemnawaveService()
        expires_at = datetime.utcnow() + timedelta(days=tariff.duration_days)
        remna_username = _make_remna_username(recipient.chat_id)

        sub = await sub_repo.create(
            user_id=recipient.id,
            remna_username=remna_username,
            tariff_type=TariffType(tariff.tariff_type),
            tariff_id=tariff.id,
            squad_uuid=tariff.squad_uuid,
            max_devices=tariff.max_devices,
        )

        payment = await payment_repo.create(
            user_id=recipient.id,
            amount_rub=0,
            subscription_id=sub.id,
            tariff_id=tariff.id,
        )

        try:
            remna_data = await remna.create_user(
                username=remna_username, expires_at=expires_at, squad_uuid=tariff.squad_uuid
            )
            short_uuid = remna_data.get("shortUuid")
            from config import settings
            sub_url = remna_data.get("subscriptionUrl") or (
                f"{settings.REMNAWAVE_PANEL_URL}/api/sub/{short_uuid}" if short_uuid else None
            )
            await sub_repo.update_remna_data(sub, remna_data.get("uuid", ""), short_uuid, sub_url, expires_at)
            await payment_repo.mark_completed(payment)
        except Exception as exc:
            logger.error("Remnawave failed during gift activation for sub %s: %s", sub.id, exc)
            await payment_repo.mark_failed(payment, reason=str(exc))

        # If recipient is new, register as sender's referral
        if gift.sender_user_id:
            await self.referral_service.register_referral(
                invited_user_id=recipient.id,
                ref_code=None,
                referrer_user_id=gift.sender_user_id,
            )

        gift = await self.gift_repo.activate(gift, recipient.id)
        return gift

    async def expire_old(self) -> int:
        return await self.gift_repo.expire_old()

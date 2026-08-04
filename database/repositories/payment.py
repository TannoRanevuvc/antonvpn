from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.payment import Payment, PaymentStatus, TopUp, TopUpStatus
from .base import BaseRepository

_TOPUP_EXPIRE_MINUTES = 60


class TopUpRepository(BaseRepository[TopUp]):
    model = TopUp

    async def get_by_payload(self, invoice_payload: str) -> TopUp | None:
        result = await self.session.execute(
            select(TopUp).where(TopUp.invoice_payload == invoice_payload)
        )
        return result.scalar_one_or_none()

    async def get_by_robokassa_inv_id(self, inv_id: int) -> TopUp | None:
        result = await self.session.execute(
            select(TopUp).where(TopUp.robokassa_inv_id == inv_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int | None, chat_id: int, amount_rub: float) -> TopUp:
        topup = TopUp(
            user_id=user_id,
            chat_id=chat_id,
            amount_rub=amount_rub,
            expires_at=datetime.utcnow() + timedelta(minutes=_TOPUP_EXPIRE_MINUTES),
        )
        topup = await self.save(topup)
        topup.invoice_payload = f"topup_{topup.id}"
        return await self.save(topup)

    async def mark_paid(self, topup: TopUp, robokassa_inv_id: int | None = None) -> TopUp:
        topup.status = TopUpStatus.PAID
        topup.paid_at = datetime.utcnow()
        if robokassa_inv_id:
            topup.robokassa_inv_id = robokassa_inv_id
        return await self.save(topup)

    async def mark_failed(self, topup: TopUp, reason: str = "") -> TopUp:
        topup.status = TopUpStatus.FAILED
        topup.fail_reason = reason
        return await self.save(topup)

    async def expire_old(self) -> int:
        from sqlalchemy import and_, update
        result = await self.session.execute(
            select(TopUp).where(
                and_(
                    TopUp.status == TopUpStatus.PENDING,
                    TopUp.expires_at < datetime.utcnow(),
                )
            )
        )
        expired = list(result.scalars().all())
        for t in expired:
            t.status = TopUpStatus.EXPIRED
            self.session.add(t)
        await self.session.commit()
        return len(expired)


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def create(
        self,
        user_id: int | None,
        amount_rub: float,
        subscription_id: int | None = None,
        tariff_id: int | None = None,
        is_renewal: bool = False,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount_rub=amount_rub,
            subscription_id=subscription_id,
            tariff_id=tariff_id,
            is_renewal=is_renewal,
        )
        return await self.save(payment)

    async def mark_completed(self, payment: Payment) -> Payment:
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        return await self.save(payment)

    async def mark_failed(self, payment: Payment, reason: str = "") -> Payment:
        payment.status = PaymentStatus.FAILED
        payment.fail_reason = reason
        return await self.save(payment)

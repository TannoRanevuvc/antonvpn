from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.payment import TopUp, TopUpStatus
from database.models.user import User
from database.repositories import TopUpRepository
from integrations.robokassa import create_invoice_url
from integrations.robokassa.exceptions import RobokassaSignatureError
from .user_service import UserService
from config import logger


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.topup_repo = TopUpRepository(session)
        self.user_service = UserService(session)

    async def create_topup_invoice(self, user: User, amount_rub: float) -> tuple[TopUp, str]:
        """Create pending TopUp record and return (topup, payment_url)."""
        topup = await self.topup_repo.create(
            user_id=user.id,
            chat_id=user.chat_id,
            amount_rub=amount_rub,
        )
        payment_url = create_invoice_url(
            inv_id=topup.id,
            amount_rub=amount_rub,
            description=f"Пополнение баланса AntonVPN #{topup.id}",
        )
        return topup, payment_url

    async def finalize_topup(self, out_sum: str, inv_id: str, signature: str) -> TopUp | None:
        """
        Called from Robokassa webhook after signature verification.
        DB-first commit pattern: update DB before any external calls.
        Idempotent: safe to call twice for the same invoice.
        """
        from integrations.robokassa import assert_result_signature
        try:
            assert_result_signature(out_sum, inv_id, signature)
        except RobokassaSignatureError:
            logger.warning("Robokassa signature mismatch for inv_id=%s", inv_id)
            return None

        topup = await self.topup_repo.get_by_robokassa_inv_id(int(inv_id))
        if topup is None:
            topup = await self.topup_repo.get_by_payload(f"topup_{inv_id}")
        if topup is None:
            logger.warning("TopUp not found for inv_id=%s", inv_id)
            return None

        if topup.status == TopUpStatus.PAID:
            return topup  # already processed, idempotent

        # DB-first: mark paid before crediting balance to avoid double-credit
        topup = await self.topup_repo.mark_paid(topup, robokassa_inv_id=int(inv_id))

        if topup.user_id:
            from database.repositories import UserRepository
            user_repo = UserRepository(self.session)
            user = await user_repo.get_by_id(topup.user_id)
            if user:
                await self.user_service.credit_balance(user, float(topup.amount_rub))

        return topup

    async def expire_old_topups(self) -> int:
        return await self.topup_repo.expire_old()

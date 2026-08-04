import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TopUpStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TopUp(Base):
    """Robokassa invoice for crediting user balance."""
    __tablename__ = "topups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    amount_rub: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    invoice_payload: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    robokassa_inv_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    status: Mapped[TopUpStatus] = mapped_column(
        Enum(TopUpStatus, name="topup_status_enum"), default=TopUpStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fail_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="topups")  # noqa: F821


class Payment(Base):
    """Internal ledger: balance debit for subscription purchase/renewal."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True)
    amount_rub: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"), default=PaymentStatus.PENDING, index=True
    )
    is_renewal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fail_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="payments")  # noqa: F821
    subscription: Mapped["Subscription | None"] = relationship("Subscription", back_populates="payments")  # noqa: F821

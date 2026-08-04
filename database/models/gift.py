import enum
import secrets
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _gen_activation_code() -> str:
    return secrets.token_urlsafe(24)


class GiftStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVATED = "activated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Gift(Base):
    __tablename__ = "gifts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sender_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recipient_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True)
    amount_rub: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    activation_code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, default=_gen_activation_code)
    status: Mapped[GiftStatus] = mapped_column(
        Enum(GiftStatus, name="gift_status_enum"), default=GiftStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sender: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[sender_user_id], back_populates="gifts_sent"
    )
    recipient: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[recipient_user_id]
    )
    tariff: Mapped["Tariff | None"] = relationship("Tariff")  # noqa: F821

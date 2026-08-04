import secrets
import string
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _gen_ref_code() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(10))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(128))
    language_code: Mapped[str] = mapped_column(String(8), default="ru", server_default="ru")
    ref_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, default=_gen_ref_code)
    balance_rub: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    blocked_bot: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="user", lazy="selectin"
    )
    topups: Mapped[list["TopUp"]] = relationship(  # noqa: F821
        "TopUp", back_populates="user", lazy="selectin"
    )
    payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        "Payment", back_populates="user", lazy="selectin"
    )
    gifts_sent: Mapped[list["Gift"]] = relationship(  # noqa: F821
        "Gift", foreign_keys="Gift.sender_user_id", back_populates="sender", lazy="selectin"
    )
    referrals_sent: Mapped[list["Referral"]] = relationship(  # noqa: F821
        "Referral", foreign_keys="Referral.referrer_user_id", back_populates="referrer", lazy="selectin"
    )
    referral_received: Mapped["Referral | None"] = relationship(  # noqa: F821
        "Referral", foreign_keys="Referral.referred_user_id", back_populates="referred", uselist=False, lazy="selectin"
    )


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referred_user_id", name="uq_referrals_referred"),
        Index("ix_referrals_referrer_id", "referrer_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referrer_user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    referred_user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    reward_credited: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    referrer: Mapped["User"] = relationship(
        "User", foreign_keys=[referrer_user_id], back_populates="referrals_sent"
    )
    referred: Mapped["User"] = relationship(
        "User", foreign_keys=[referred_user_id], back_populates="referral_received"
    )

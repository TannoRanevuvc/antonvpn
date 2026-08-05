from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ReferralReward(Base):
    """One row per referral commission credited to a beneficiary from a payer's top-up."""
    __tablename__ = "referral_rewards"
    __table_args__ = (
        Index("ix_ref_reward_beneficiary_payer", "beneficiary_id", "payer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topup_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topups.id", ondelete="SET NULL"), nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or 2
    amount_rub: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    beneficiary: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[beneficiary_id]
    )
    payer: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[payer_id]
    )

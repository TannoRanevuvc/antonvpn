from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .subscription import TariffType


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    tariff_type: Mapped[TariffType] = mapped_column(Enum(TariffType, name="tariff_type_enum"), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price_rub: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_devices: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    squad_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now()
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="tariff", lazy="selectin"
    )

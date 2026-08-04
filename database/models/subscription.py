import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RemnaStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class TariffType(str, enum.Enum):
    VPN = "VPN"
    OBFUSCATED = "OBFUSCATED"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remna_uuid: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    remna_username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    remna_short_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remna_sub_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    remna_status: Mapped[RemnaStatus] = mapped_column(
        Enum(RemnaStatus, name="remna_status_enum"), default=RemnaStatus.ACTIVE
    )
    squad_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tariff_type: Mapped[TariffType] = mapped_column(Enum(TariffType, name="tariff_type_enum"), nullable=False)
    max_devices: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sub_remind_3d_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sub_remind_1d_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sub_remind_1h_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sub_expired_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")  # noqa: F821
    tariff: Mapped["Tariff | None"] = relationship("Tariff", back_populates="subscriptions")  # noqa: F821
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="subscription", lazy="selectin")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="subscription", lazy="selectin")  # noqa: F821


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remna_device_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    os: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    client_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="devices")

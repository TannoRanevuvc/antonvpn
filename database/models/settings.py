from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BotSettings(Base):
    __tablename__ = "bot_settings"

    # Non-mapped sentinel so sqladmin's _handle_form_data doesn't crash
    # on the oferta_upload FileField that has no corresponding model column.
    oferta_upload = None

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    registration_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    trial_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    site_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    news_channel_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    support_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bot_description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bot_short_description: Mapped[str | None] = mapped_column(String(120), nullable=True)
    oferta_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bot_photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    trial_squad_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_squad_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now()
    )


class ReferralSettings(Base):
    __tablename__ = "referral_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    level1_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=15, server_default="15")
    level2_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=5, server_default="5")
    max_paid_topups: Mapped[int] = mapped_column(Integer, default=2, server_default="2")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now()
    )


class ChannelSettings(Base):
    __tablename__ = "channel_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    channel_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now()
    )

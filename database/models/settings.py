from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BotSettings(Base):
    __tablename__ = "bot_settings"

    # Non-mapped sentinels so sqladmin's _handle_form_data doesn't crash on
    # extra FileFields that don't correspond to model columns.
    oferta_upload = None
    bot_photo_upload = None

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
    reward_type: Mapped[str] = mapped_column(String(16), default="balance", server_default="balance")
    reward_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    max_rewards_per_referrer: Mapped[int | None] = mapped_column(Integer, nullable=True)
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

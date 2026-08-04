"""init

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False),
        sa.Column("chat_id", sa.BigInteger, nullable=False),
        sa.Column("first_name", sa.String(128), nullable=True),
        sa.Column("username", sa.String(128), nullable=True),
        sa.Column("language_code", sa.String(8), server_default="ru", nullable=False),
        sa.Column("ref_code", sa.String(16), nullable=False),
        sa.Column("balance_rub", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("is_banned", sa.Boolean, server_default="false", nullable=False),
        sa.Column("blocked_bot", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("last_activity", sa.DateTime, nullable=True),
    )
    op.create_unique_constraint("uq_users_telegram_id", "users", ["telegram_id"])
    op.create_unique_constraint("uq_users_chat_id", "users", ["chat_id"])
    op.create_unique_constraint("uq_users_ref_code", "users", ["ref_code"])
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])
    op.create_index("ix_users_chat_id", "users", ["chat_id"])

    # referrals
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("referrer_user_id", sa.BigInteger, nullable=False),
        sa.Column("referred_user_id", sa.BigInteger, nullable=False),
        sa.Column("reward_credited", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_referrals_referred", "referrals", ["referred_user_id"])
    op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_user_id"])

    # tariffs
    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("tariff_type", sa.String(32), nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("price_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_devices", sa.Integer, server_default="1", nullable=False),
        sa.Column("squad_uuid", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tariff_id", sa.Integer, sa.ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("display_name", sa.String(64), nullable=True),
        sa.Column("remna_uuid", sa.String(64), unique=True, nullable=True),
        sa.Column("remna_username", sa.String(64), unique=True, nullable=False),
        sa.Column("remna_short_uuid", sa.String(64), nullable=True),
        sa.Column("remna_sub_url", sa.String(512), nullable=True),
        sa.Column("remna_status", sa.String(16), server_default="ACTIVE", nullable=False),
        sa.Column("squad_uuid", sa.String(64), nullable=True),
        sa.Column("tariff_type", sa.String(32), nullable=False),
        sa.Column("max_devices", sa.Integer, server_default="1", nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("auto_renewal", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sub_remind_3d_sent", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sub_remind_1d_sent", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sub_remind_1h_sent", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sub_expired_sent", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_expires_at", "subscriptions", ["expires_at"])

    # devices
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer, sa.ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("remna_device_id", sa.String(128), unique=True, nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("os", sa.String(64), nullable=True),
        sa.Column("os_version", sa.String(32), nullable=True),
        sa.Column("client_version", sa.String(32), nullable=True),
        sa.Column("last_seen", sa.DateTime, nullable=True),
        sa.Column("synced_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_devices_subscription_id", "devices", ["subscription_id"])

    # topups
    op.create_table(
        "topups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chat_id", sa.BigInteger, nullable=False),
        sa.Column("amount_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("invoice_payload", sa.String(128), unique=True, nullable=False),
        sa.Column("robokassa_inv_id", sa.Integer, unique=True, nullable=True),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("fail_reason", sa.String(256), nullable=True),
    )
    op.create_index("ix_topups_user_id", "topups", ["user_id"])
    op.create_index("ix_topups_chat_id", "topups", ["chat_id"])
    op.create_index("ix_topups_status", "topups", ["status"])

    # payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subscription_id", sa.Integer, sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tariff_id", sa.Integer, sa.ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("is_renewal", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("fail_reason", sa.String(256), nullable=True),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    # gifts
    op.create_table(
        "gifts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sender_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipient_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tariff_id", sa.Integer, sa.ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("activation_code", sa.String(48), unique=True, nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("activated_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_gifts_sender_user_id", "gifts", ["sender_user_id"])

    # message_templates
    op.create_table(
        "message_templates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(128), unique=True, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("image_path", sa.String(512), nullable=True),
    )
    op.create_index("ix_message_templates_key", "message_templates", ["key"])

    # notification_rules
    op.create_table(
        "notification_rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("hours_before_expiry", sa.Integer, nullable=False),
        sa.Column("message_template_key", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # bot_settings
    op.create_table(
        "bot_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("registration_enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("trial_days", sa.Integer, server_default="0", nullable=False),
        sa.Column("site_url", sa.String(256), nullable=True),
        sa.Column("news_channel_url", sa.String(256), nullable=True),
        sa.Column("support_url", sa.String(256), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # referral_settings
    op.create_table(
        "referral_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("is_enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("reward_type", sa.String(16), server_default="balance", nullable=False),
        sa.Column("reward_amount", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("max_rewards_per_referrer", sa.Integer, nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # channel_settings
    op.create_table(
        "channel_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("is_enabled", sa.Boolean, server_default="false", nullable=False),
        sa.Column("channel_id", sa.BigInteger, nullable=True),
        sa.Column("channel_url", sa.String(256), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("channel_settings")
    op.drop_table("referral_settings")
    op.drop_table("bot_settings")
    op.drop_table("notification_rules")
    op.drop_table("message_templates")
    op.drop_table("gifts")
    op.drop_table("payments")
    op.drop_table("topups")
    op.drop_table("devices")
    op.drop_table("subscriptions")
    op.drop_table("tariffs")
    op.drop_table("referrals")
    op.drop_table("users")

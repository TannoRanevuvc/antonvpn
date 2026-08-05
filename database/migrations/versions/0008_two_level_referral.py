"""two-level referral system

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # referral_rewards audit table
    op.create_table(
        "referral_rewards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("beneficiary_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payer_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topup_id", sa.Integer, sa.ForeignKey("topups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("amount_rub", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ref_reward_beneficiary_payer", "referral_rewards", ["beneficiary_id", "payer_id"])
    op.create_index("ix_ref_reward_beneficiary_id", "referral_rewards", ["beneficiary_id"])
    op.create_index("ix_ref_reward_payer_id", "referral_rewards", ["payer_id"])

    # replace old referral_settings columns with percent-based ones
    op.add_column("referral_settings", sa.Column("level1_percent", sa.Numeric(5, 2), server_default="15", nullable=False))
    op.add_column("referral_settings", sa.Column("level2_percent", sa.Numeric(5, 2), server_default="5", nullable=False))
    op.add_column("referral_settings", sa.Column("max_paid_topups", sa.Integer, server_default="2", nullable=False))
    op.drop_column("referral_settings", "reward_type")
    op.drop_column("referral_settings", "reward_amount")
    op.drop_column("referral_settings", "max_rewards_per_referrer")


def downgrade() -> None:
    op.add_column("referral_settings", sa.Column("reward_type", sa.String(16), server_default="balance", nullable=False))
    op.add_column("referral_settings", sa.Column("reward_amount", sa.Numeric(10, 2), server_default="0", nullable=False))
    op.add_column("referral_settings", sa.Column("max_rewards_per_referrer", sa.Integer, nullable=True))
    op.drop_column("referral_settings", "level1_percent")
    op.drop_column("referral_settings", "level2_percent")
    op.drop_column("referral_settings", "max_paid_topups")
    op.drop_table("referral_rewards")

"""add squad uuids to bot_settings and is_trial to subscriptions

Revision ID: 0005
Revises: 0004
Create Date: 2024-01-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_settings", sa.Column("trial_squad_uuid", sa.String(64), nullable=True))
    op.add_column("bot_settings", sa.Column("default_squad_uuid", sa.String(64), nullable=True))
    op.add_column("subscriptions", sa.Column("is_trial", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("bot_settings", "trial_squad_uuid")
    op.drop_column("bot_settings", "default_squad_uuid")
    op.drop_column("subscriptions", "is_trial")

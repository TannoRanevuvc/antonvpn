"""add bot_photo_path to bot_settings

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_settings", sa.Column("bot_photo_path", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("bot_settings", "bot_photo_path")

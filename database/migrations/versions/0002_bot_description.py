"""add bot description fields

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_settings", sa.Column("bot_description", sa.String(512), nullable=True))
    op.add_column("bot_settings", sa.Column("bot_short_description", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("bot_settings", "bot_short_description")
    op.drop_column("bot_settings", "bot_description")

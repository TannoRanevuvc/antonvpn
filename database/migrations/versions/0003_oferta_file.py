"""add oferta_file_path to bot_settings

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_settings", sa.Column("oferta_file_path", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("bot_settings", "oferta_file_path")

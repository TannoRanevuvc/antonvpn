"""add consent_at to users

Revision ID: 0007
Revises: 0006
Create Date: 2024-01-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("consent_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "consent_at")

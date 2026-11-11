"""Add published slug to posts.

Revision ID: ab42d13f6c09
Revises: d8f4c6a1b2e3
"""

from alembic import op
import sqlalchemy as sa


revision = "ab42d13f6c09"
down_revision = "d8f4c6a1b2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("published_slug", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "published_slug")

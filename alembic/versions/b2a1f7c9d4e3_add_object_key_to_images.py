"""add object key to images

Revision ID: b2a1f7c9d4e3
Revises: 7a2f1c4b8d9e
Create Date: 2026-04-10 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2a1f7c9d4e3"
down_revision: Union[str, Sequence[str], None] = "7a2f1c4b8d9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("images", sa.Column("object_key", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("images", "object_key")

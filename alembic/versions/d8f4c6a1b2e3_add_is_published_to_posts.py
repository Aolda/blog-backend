"""add is published to posts

Revision ID: d8f4c6a1b2e3
Revises: b2a1f7c9d4e3
Create Date: 2026-07-17 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8f4c6a1b2e3"
down_revision: Union[str, Sequence[str], None] = "b2a1f7c9d4e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "posts",
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("posts", "is_published")

"""add post content and images table

Revision ID: 9f8c1d2e4a11
Revises: 6438ad19d6f0
Create Date: 2026-02-26 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f8c1d2e4a11"
down_revision: Union[str, Sequence[str], None] = "6438ad19d6f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("content", sa.Text(), nullable=True))

    op.create_table(
        "images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_images_id"), "images", ["id"], unique=False)
    op.create_index(op.f("ix_images_post_id"), "images", ["post_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_images_post_id"), table_name="images")
    op.drop_index(op.f("ix_images_id"), table_name="images")
    op.drop_table("images")
    op.drop_column("posts", "content")

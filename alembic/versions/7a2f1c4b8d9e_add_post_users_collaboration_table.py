"""add post users collaboration table

Revision ID: 7a2f1c4b8d9e
Revises: c3f9c8d7e1ab
Create Date: 2026-04-02 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a2f1c4b8d9e"
down_revision: Union[str, Sequence[str], None] = "c3f9c8d7e1ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_users",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO post_users (post_id, user_id)
            SELECT id, author_id
            FROM posts
            WHERE author_id IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_table("post_users")

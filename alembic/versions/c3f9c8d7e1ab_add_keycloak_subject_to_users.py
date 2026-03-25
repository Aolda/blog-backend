"""add keycloak subject to users

Revision ID: c3f9c8d7e1ab
Revises: 9792e1fb44ac
Create Date: 2026-03-22 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3f9c8d7e1ab"
down_revision: Union[str, Sequence[str], None] = "9792e1fb44ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("keycloak_sub", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_keycloak_sub"), "users", ["keycloak_sub"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_keycloak_sub"), table_name="users")
    op.drop_column("users", "keycloak_sub")

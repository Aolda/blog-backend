from sqlalchemy import Column, ForeignKey, Integer, Table

from app.db.database import Base


post_users = Table(
    "post_users",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

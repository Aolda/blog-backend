from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    image = Column(String(2048), nullable=True)
    content = Column(Text, nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    author = relationship("User", back_populates="posts")
    images = relationship(
        "Image",
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=True) # 마크다운 원본
    summary = Column(String(1000), nullable=True) # 요약 (자동)
    thumbnail = Column(String(255), nullable=True) # 썸네일 이미지 (선택)
    views = Column(Integer, default=0)

    # 게시글 상태
    status = Column(Enum("draft", "published", name="post_status_enum"), 
                    nullable=False, default="draft", index=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계: User (1:N)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False) # 외래 키
    author = relationship("User", back_populates="posts") # ORM 관계

    # 관계: Category (1:N)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True) # 외래 키
    category = relationship("Category", back_populates="posts") # ORM 관계
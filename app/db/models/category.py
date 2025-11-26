from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # 카테고리 이름

    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True) # 외래 키 (스스로 참조)
    parent = relationship("Category", remote_side=[id], back_populates="children") # 부모 관계
    children = relationship("Category", back_populates="parent") # 자식 관계

    # Post와 관계 (1:N)
    posts = relationship("Post", back_populates="category")
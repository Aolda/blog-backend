from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False) # 비밀번호는 해시로 저장

    name = Column(String(100), nullable=True)
    bio = Column(String(500), nullable=True) # 자기소개
    profile = Column(String(255), nullable=True) # 프로필 사진 URL

    role = Column(String(50), nullable=False, default="writer")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계 설정 (1:N)
    # 'User' 모델에서 'Post' 모델을 참조할 때 사용할 이름
    # back_populates는 Post 모델에서 User를 참조할 이름
    posts = relationship("Post", back_populates="author")

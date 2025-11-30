from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.db.schemas.user import User  
from app.db.schemas.category import Category

# PostBase
class PostBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    thumbnail: Optional[str] = None
    status: str = "draft" # 기본값 '임시저장'
    category_id: Optional[int] = None

# PostCreate (생성용)
# POST /api/posts
class PostCreate(PostBase):
    pass # PostBase와 동일

# PostUpdate (수정용)
# PUT /api/posts/{post_id}
class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    thumbnail: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None

# Post (조회용 - 중첩 스키마)
# API가 게시글 정보를 응답(Response)할 때 사용
# (예: GET /api/posts, GET /api/posts/{post_id})
class Post(PostBase):
    id: int
    views: int = 0
    created_at: datetime
    updated_at: datetime
    
    # 중첩된 작성자 및 카테고리 정보
    author: User # User 스키마를 중첩 (비밀번호 제외된 정보)
    category: Optional[Category] = None # Category 스키마를 중첩

    model_config = ConfigDict(from_attributes=True)
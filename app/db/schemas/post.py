from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PostTemplateResponse(BaseModel):
    post_id: int


class PostContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    content: str
    authors: Optional[List[str]] = None


class PostSummaryResponse(BaseModel):
    id: int
    author_id: Optional[int] = None
    authors: List[str] = Field(default_factory=list)
    can_edit: bool = False
    views: int = 0
    created_at: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image: Optional[str] = None


class PostResponse(PostSummaryResponse):
    content: Optional[str] = None


class PaginatedPostsResponse(BaseModel):
    items: List[PostSummaryResponse] = Field(default_factory=list)
    page: int
    limit: int
    total: int

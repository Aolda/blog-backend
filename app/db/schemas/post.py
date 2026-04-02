from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PostTemplateResponse(BaseModel):
    post_id: int
    author_name: str
    author_names: List[str] = Field(default_factory=list)
    created_at: str
    frontmatter_example: str


class PostContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    content: str
    authors: Optional[List[str]] = None


class PostFrontmatter(BaseModel):
    title: str
    description: str
    date: str
    tags: List[str]
    image: str
    author: List[str]


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
    frontmatter: PostFrontmatter
    frontmatter_header: str


class PostResponse(PostSummaryResponse):
    content: Optional[str] = None

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PostTemplateResponse(BaseModel):
    post_id: int
    author_name: str
    created_at: str
    frontmatter_example: str


class PostContentUpdate(BaseModel):
    content: str


class PostSummaryResponse(BaseModel):
    id: int
    author_id: Optional[int] = None
    views: Optional[int] = 0
    created_at: datetime
    content: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostResponse(PostSummaryResponse):
    pass

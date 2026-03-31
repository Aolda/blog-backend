from pydantic import BaseModel
from datetime import datetime

# 템플릿 응답용 스키마
class PostTemplateResponse(BaseModel):
    post_id: int
    author_name: str
    created_at: str
    
    # 프론트가 MDX 만들 때 복붙하기 좋게 미리 포맷팅된 예시 주기
    frontmatter_example: str 

class Config:
    from_attributes = True
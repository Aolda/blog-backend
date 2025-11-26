from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# CategoryBase (공통)
class CategoryBase(BaseModel):
    name: str

# CategoryCreate (생성용)
# POST /api/admin/categories
class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None # 부모 카테고리 ID

# Category (조회용 - 재귀적 구조)
# GET /api/admin/categories, GET /api/categories
class Category(CategoryBase):
    id: int
    parent_id: Optional[int] = None
    
    # 자식 카테고리 목록을 재귀적으로 포함
    children: List['Category'] = [] 

    model_config = ConfigDict(from_attributes=True)
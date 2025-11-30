from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Category as CategoryModel, User as UserModel
from app.db.schemas.category import CategoryCreate, Category as CategorySchema
from app.api.deps import get_current_admin

router = APIRouter()

@router.get("/", response_model=List[CategorySchema])
def read_categories(
    page: int = 1,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    카테고리 목록 조회 API
    """
    
    skip = (page - 1) * limit
    
    categories = db.query(CategoryModel).offset(skip).limit(limit).all()
    return categories

@router.post("/", response_model=CategorySchema, status_code=201)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin) # 관리자 체크
):
    """
    카테고리 생성 API
    """
    # 중복 체크
    if db.query(CategoryModel).filter(CategoryModel.name == category_in.name).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 카테고리입니다.")
        
    category = CategoryModel(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    """
    카테고리 수정 API
    """
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
        
    category.name = category_in.name
    category.parent_id = category_in.parent_id
    
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    """
    카테고리 삭제 API
    """
    
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
        
    db.delete(category)
    db.commit()
    return None
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User as UserModel
from app.db.schemas.user import User as UserSchema, UserUpdate
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    내 프로필 조회 API
    - 현재 로그인한 사용자 정보 반환.
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    내 프로필 수정 API
    - 이름(닉네임), 자기소개, 프로필 사진 URL 수정.
    - 입력된 값만 업데이트.
    """
    
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "username" in update_data:
        del update_data["username"]
    
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/", response_model=List[UserSchema])
def read_users(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    전체 사용자 목록 조회 API
    """
    
    skip = (page - 1) * limit
    
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.get("/{username}", response_model=UserSchema)
def read_user_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    """
    특정 사용자 프로필 조회 API
    - username(아이디)으로 사용자를 찾아 정보를 반환합니다.
    """
    user = db.query(UserModel).filter(UserModel.username == username).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
        
    return user
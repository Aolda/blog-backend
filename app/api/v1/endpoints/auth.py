from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User as UserModel
from app.db.schemas.user import UserCreate, User as UserSchema, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입 API

    - **username**: 아이디 (고유값)
    - **email**: 이메일 주소 (고유값)
    - **password**: 비밀번호 (해싱)
    - **name**: 사용자 이름 (닉네임)
    """
    
    # 이메일 중복 확인
    user_by_email = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다."
        )
    
    # username(아이디) 중복 확인
    user_by_username = db.query(UserModel).filter(UserModel.username == user_in.username).first()
    if user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 아이디입니다."
        )
        
    # 비밀번호 해싱 및 사용자 생성
    user_dict = user_in.model_dump(exclude={"password"})
    hashed_password = get_password_hash(user_in.password)
    
    new_user = UserModel(
        **user_dict,
        hashed_password=hashed_password,
        role="writer"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    로그인 API
    - 이메일과 비밀번호를 받아 검증합니다.
    - 성공 시 JWT 액세스 토콘을 발급합니다.
    """
    
    # 이메일로 사용자 찾기
    # form_data는 필드명이 무조건 'username' (db의 username이 아님)
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    
    # 사용자가 없거나 비밀번호가 틀린 경우 체크
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 토큰 만료 시간
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # JWT 토큰 생성
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    현재 로그인된 사용자 정보 조회 API
    - 헤더에 유효한 JWT이 있어야 접근 가능합니다.
    """
    return current_user
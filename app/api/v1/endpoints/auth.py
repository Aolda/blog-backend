from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User as UserModel
from app.db.schemas.user import UserCreate, User as UserSchema, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from jose import jwt, JWTError

router = APIRouter()


def get_user_by_subject(db: Session, subject: str) -> UserModel | None:
    user = db.query(UserModel).filter(UserModel.keycloak_sub == subject).first()
    if user is not None:
        return user
    return db.query(UserModel).filter(UserModel.username == subject).first()

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
            detail="이미 존재하는 사용자 이름입니다."
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
    user_in: UserLogin,
    db: Session = Depends(get_db)
):
    """
    로그인 API
    - 이메일과 비밀번호를 받아 검증합니다.
    - 성공 시 JWT 액세스 토큰을 발급합니다.
    """
    
    # 이메일로 사용자 찾기
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    
    # 사용자가 없거나 비밀번호가 틀린 경우 체크
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 토큰 만료 시간
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 액세스 토큰 생성
    access_token = create_access_token(
        data={"sub": user.keycloak_sub or user.username},
        expires_delta=access_token_expires
    )
    
    # 리프레시 토큰 생성
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(
        data={"sub": user.keycloak_sub or user.username},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }
    
@router.post("/logout")
def logout():
    return {"message": "로그아웃 되었습니다."}
    
@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    토큰 갱신 API
    - 리프레시 토큰을 발급받아 유효성을 검증하고 새로운 액세스 토큰을 발급합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 리프레시 토큰 유효성 검증
        payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_subject(db, subject)
    if user is None:
        raise credentials_exception
    
    # 새로운 액세스 토큰 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.keycloak_sub or user.username},
        expires_delta=access_token_expires
    )
    
    # 기존 리프레시 토큰 반환
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

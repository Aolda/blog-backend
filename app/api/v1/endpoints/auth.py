from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User as UserModel
from app.db.schemas.user import Token
from app.core.security import create_access_token
from jose import jwt, JWTError

router = APIRouter()


def get_user_by_subject(db: Session, subject: str) -> UserModel | None:
    user = db.query(UserModel).filter(UserModel.keycloak_sub == subject).first()
    if user is not None:
        return user
    return db.query(UserModel).filter(UserModel.username == subject).first()

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

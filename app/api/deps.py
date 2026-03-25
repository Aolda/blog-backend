from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models.user import User
from app.core.security import TokenData

security = HTTPBearer()

def get_user_by_subject(db: Session, subject: str) -> User | None:
    user = db.query(User).filter(User.keycloak_sub == subject).first()
    if user is not None:
        return user
    return db.query(User).filter(User.username == subject).first()


# 현재 사용자 가져오기
def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials # Bearer 부분을 뗀 순수 토큰 값
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 디코딩
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise credentials_exception
        token_data = TokenData(subject=subject)
    except JWTError:
        raise credentials_exception
    
    # DB에서 사용자 확인
    user = get_user_by_subject(db, token_data.subject)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user

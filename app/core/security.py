from passlib.context import CryptContext

# 사용할 해시 알고리즘 설정 (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 비밀번호 해시 함수
def get_password_hash(password: str) -> str:
    """일반 텍스트 비밀번호를 해시하여 반환합니다."""
    return pwd_context.hash(password)

# 비밀번호 검증 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """일반 텍스트 비밀번호와 해시된 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

class TokenData(BaseModel):
    username: Optional[str] = None

# 액세스 토큰 생성 함수
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 설정 파일에서 토큰 만료 시간 가져오기
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    
    # 설정 파일에서 시크릿 키와 알고리즘 가져오기
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

# 리프레시 토큰 생성
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 설정 파일에서 토큰 만료 시간 가져오기
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    
    # 설정 파일에서 시크릿 키와 알고리즘 가져오기
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
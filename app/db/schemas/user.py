from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# UserBase (공통 스키마)
# UserCreate와 User가 공통으로 가질 필드
class UserBase(BaseModel):
    username: str
    email: EmailStr # pydantic[email]로 이메일 형식을 자동 검증
    name: Optional[str] = None

# UserCreate (생성용 스키마)
# 회원가입(POST /api/auth/register) 시 받을 데이터
class UserCreate(UserBase):
    password: str # 비밀번호는 생성 시에만 받음

# UserUpdate (수정용 스키마)
# 본인 프로필 수정(PUT /api/profile) 시 받을 데이터
class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    profile: Optional[str] = None
    # 비밀번호 변경은 보안을 위해 별도 API로 분리

# User (조회용 스키마)
# API가 사용자 정보를 응답(Response)할 때 사용할 스키마
class User(UserBase):
    id: int
    bio: Optional[str] = None
    profile: Optional[str] = None
    role: str
    created_at: datetime
    updated_at: datetime

    # ORM 모드 설정
    model_config = ConfigDict(from_attributes=True)
    
# UserLogin (로그인 요청용)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token (로그인 응답용)
class Token(BaseModel):
    access_token: str
    token_type: str
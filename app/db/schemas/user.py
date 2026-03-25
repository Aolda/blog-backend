from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime

# UserCreate와 User가 공통으로 가질 필드
class UserBase(BaseModel):
    username: str
    email: EmailStr # pydantic[email]로 이메일 형식을 자동 검증
    name: Optional[str] = None

# 회원가입(POST /api/auth/register) 시 받을 데이터
class UserCreate(UserBase):
    password: str # 비밀번호는 생성 시에만 받음

# 본인 프로필 수정(PUT /api/profile) 시 받을 데이터
class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    
    website: Optional[str] = None
    github: Optional[str] = None
    gitlab: Optional[str] = None
    linkedin: Optional[str] = None
    discord: Optional[str] = None
    mail: Optional[str] = None
    

# API가 사용자 정보를 응답(Response)할 때 사용할 스키마
class User(UserBase):
    id: int
    keycloak_sub: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    
    website: Optional[str] = None
    github: Optional[str] = None
    gitlab: Optional[str] = None
    linkedin: Optional[str] = None
    discord: Optional[str] = None
    mail: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    # ORM 모드 설정
    model_config = ConfigDict(from_attributes=True)
    
class AuthorResponse(BaseModel):
    id: str
    username: str
    name: Optional[str] = None
    
    bio: str
    avatar: str

    website: Optional[str] = None
    github: Optional[str] = None
    gitlab: Optional[str] = None
    linkedin: Optional[str] = None
    discord: Optional[str] = None
    mail: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def map_username_to_public_id(cls, value):
        if hasattr(value, "username"):
            return {
                "id": value.username,
                "username": value.username,
                "name": value.name,
                "bio": value.bio,
                "avatar": value.avatar,
                "website": value.website,
                "github": value.github,
                "gitlab": value.gitlab,
                "linkedin": value.linkedin,
                "discord": value.discord,
                "mail": value.mail,
            }
        return value

    @field_validator('name', mode='before')
    @classmethod
    def set_default_name(cls, v, info):
        return v or info.data.get('username')

    # DB에서 None이 넘어오면 -> 빈 문자열로 변환
    @field_validator('bio', mode='before')
    @classmethod
    def set_default_bio(cls, v):
        return v or ""

    # DB에서 None이 넘어오면 -> 기본 이미지로 변환
    @field_validator('avatar', mode='before')
    @classmethod
    def set_default_avatar(cls, v, info):
        if not v:
            name = info.data.get('name', 'User')
            return f"https://ui-avatars.com/api/?name={name}&background=random"
        return v

    model_config = ConfigDict(from_attributes=True)
    
# 로그인 요청용
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 로그인 응답용
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

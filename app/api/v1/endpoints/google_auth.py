import uuid
from typing import Optional
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, Depends, HTTPException, status, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from jose import jwt, JWTError

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User as UserModel
from app.core.security import create_access_token, create_refresh_token, get_password_hash

router = APIRouter()

# 설정 및 모델 정의
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

class GoogleRegisterRequest(BaseModel):
    username: str
    register_token: str
    
# 구글 로그인 및 콜백
@router.get("/login")
async def google_login(request: Request):
    """
    1. 구글 로그인 페이지로 이동
    """
    redirect_uri = "http://localhost:8000/api/v1/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    2. 구글 인증 후 처리
    - 이미 가입된 유저 -> 바로 로그인 (Home으로 이동)
    - 신규 유저 -> 임시 토큰 발급 후 '닉네임 설정 페이지'로 이동
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="구글 로그인 실패")
    
    user_info = token.get('userinfo')
    email = user_info.get('email')
    
    if not email:
        raise HTTPException(status_code=400, detail="이메일 정보를 가져올 수 없습니다.")

    # DB 확인
    user = db.query(UserModel).filter(UserModel.email == email).first()

    # 이미 가입된 사용자 -> 로그인 성공 처리
    if user:
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        # 로그인 성공 페이지로 이동 (토큰 전달)
        return RedirectResponse(
            url=f"http://localhost:1234/auth/callback?status=success&access_token={access_token}&refresh_token={refresh_token}"
        )

    # 신규 사용자 -> 회원가입용 임시 토큰 발급 (유효기간 10분)
    # 이 토큰에는 "이메일 정보"만 들어있음. username은 아직 없음.
    register_token_expires = timedelta(minutes=10)
    register_payload = {
        "sub": email,          # 이메일을 식별자로 저장
        "type": "google_register", # 용도 명시
        "exp": datetime.utcnow() + register_token_expires
    }
    register_token = jwt.encode(register_payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # 닉네임 설정 페이지로 이동 (임시 토큰 전달)
    return RedirectResponse(
        url=f"http://localhost:1234/register/google?token={register_token}&email={email}"
    )
    
@router.post("/finish", status_code=status.HTTP_201_CREATED)
def finish_google_register(
    req: GoogleRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    3. 닉네임 입력 후 최종 가입
    - 프론트에서 받은 임시 토큰을 검증해서 이메일을 꺼냄
    - 입력받은 'username'으로 계정 생성
    """
    
    # 임시 토큰 검증 및 이메일 추출
    try:
        payload = jwt.decode(req.register_token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        
        if not email or token_type != "google_register":
            raise HTTPException(status_code=400, detail="유효하지 않은 가입 토큰입니다.")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="토큰이 만료되었거나 유효하지 않습니다.")

    # 이미 가입된 이메일인지 재확인
    if db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    # username 중복 확인
    if db.query(UserModel).filter(UserModel.username == req.username).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

    # 최종 사용자 생성
    new_user = UserModel(
        email=email,
        username=req.username, # 사용자가 직접 입력한 값
        hashed_password=get_password_hash(str(uuid.uuid4())), # 비밀번호는 랜덤 처리
        role="writer"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 로그인 토큰 발급
    access_token = create_access_token(data={"sub": new_user.username})
    refresh_token = create_refresh_token(data={"sub": new_user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "username": new_user.username,
        "message": "회원가입이 완료되었습니다."
    }
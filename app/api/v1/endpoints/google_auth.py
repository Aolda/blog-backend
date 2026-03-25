import re
import uuid
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User as UserModel
from app.core.security import create_access_token, create_refresh_token, get_password_hash

router = APIRouter()

# 설정 및 모델 정의
oauth = OAuth()
oauth.register(
    name="keycloak",
    client_id=settings.KEYCLOAK_CLIENT_ID,
    client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    server_metadata_url=f"{settings.KEYCLOAK_ISSUER_URI}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def normalize_username(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:50] or "writer"


def sanitize_preferred_username(value: str | None) -> str:
    if not value:
        return ""
    if "@" in value:
        return value.split("@")[0]
    return value


def generate_unique_username(db: Session, *candidates: str) -> str:
    for candidate in candidates:
        if not candidate:
            continue
        base_username = normalize_username(candidate)
        username = base_username
        suffix = 1
        while db.query(UserModel).filter(UserModel.username == username).first():
            suffix += 1
            username = f"{base_username[:50 - len(str(suffix)) - 1]}-{suffix}"
        return username
    return generate_unique_username(db, "writer")


def extract_claims(token: dict[str, Any]) -> dict[str, str | None]:
    userinfo = token.get("userinfo") or {}
    id_token_claims = token.get("id_token_claims") or {}
    return {
        "sub": userinfo.get("sub") or id_token_claims.get("sub"),
        "email": userinfo.get("email") or id_token_claims.get("email"),
        "preferred_username": (
            userinfo.get("preferred_username") or id_token_claims.get("preferred_username")
        ),
        "name": userinfo.get("name") or id_token_claims.get("name"),
        "picture": userinfo.get("picture") or id_token_claims.get("picture"),
    }


async def load_claims_from_keycloak(request: Request, token: dict[str, Any]) -> dict[str, Any]:
    parse_error: Exception | None = None
    userinfo_error: Exception | None = None

    if token.get("id_token"):
        try:
            token["id_token_claims"] = await oauth.keycloak.parse_id_token(request, token)
            return token
        except Exception as exc:
            parse_error = exc

    try:
        token["userinfo"] = await oauth.keycloak.userinfo(token=token)
        return token
    except Exception as exc:
        userinfo_error = exc

    raise HTTPException(
        status_code=400,
        detail=(
            "Keycloak 사용자 정보 조회 실패 "
            f"(id_token parse: {parse_error!r}, userinfo: {userinfo_error!r})"
        ),
    )


def build_frontend_callback_url(access_token: str, refresh_token: str) -> str:
    return (
        f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback"
        f"?status=success&access_token={access_token}&refresh_token={refresh_token}"
    )


@router.get("/login")
async def google_login(request: Request):
    """
    Keycloak 로그인 페이지로 이동
    """
    redirect_uri = settings.KEYCLOAK_REDIRECT_URI
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="google_auth_callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Keycloak 인증 후 처리
    - keycloak_sub로 기존 유저 조회
    - 없으면 이메일로 기존 계정 1회 연결
    - 둘 다 없으면 신규 유저 자동 생성
    """
    try:
        token = await oauth.keycloak.authorize_access_token(request)
        token = await load_claims_from_keycloak(request, token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Keycloak 로그인 실패: {exc!r}") from exc

    claims = extract_claims(token)
    keycloak_sub = claims.get("sub")
    email = claims.get("email")

    if not keycloak_sub:
        raise HTTPException(status_code=400, detail="Keycloak sub 값을 가져올 수 없습니다.")

    user = db.query(UserModel).filter(UserModel.keycloak_sub == keycloak_sub).first()

    if user is None and email:
        user = (
            db.query(UserModel)
            .filter(UserModel.email == email, UserModel.keycloak_sub.is_(None))
            .first()
        )

    if user is None:
        username = generate_unique_username(
            db,
            (email or "").split("@")[0],
            sanitize_preferred_username(claims.get("preferred_username")),
            claims.get("name") or "",
        )
        user = UserModel(
            keycloak_sub=keycloak_sub,
            email=email or f"{username}@local.invalid",
            username=username,
            hashed_password=get_password_hash(str(uuid.uuid4())),
            name=claims.get("name"),
            avatar=claims.get("picture"),
            role="writer",
        )
    else:
        user.keycloak_sub = keycloak_sub
        if email:
            user.email = email
            user.mail = user.mail or email
        if claims.get("name"):
            user.name = claims["name"]
        if claims.get("picture"):
            user.avatar = claims["picture"]

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return RedirectResponse(url=build_frontend_callback_url(access_token, refresh_token))


@router.post("/finish", status_code=status.HTTP_410_GONE)
def finish_google_register():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="신규 회원가입은 Keycloak에서 처리됩니다.",
    )

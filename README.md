# ABS Backend

ABS(Aolda Blog Service) 백엔드 API 서버입니다.  
블로그 게시글, 이미지, 사용자, 인증 기능을 제공하며 FastAPI 기반으로 동작합니다.

## 기술 스택

- Python
- FastAPI
- SQLAlchemy
- Alembic
- MySQL
- boto3
- Authlib

## 프로젝트 구조

```text
abs-backend/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── api_router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── images.py
│   │           ├── keycloak_auth.py
│   │           ├── posts.py
│   │           └── users.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models/
│   │   └── schemas/
│   ├── services/
│   └── main.py
├── alembic/
│   └── versions/
├── compose.yaml
├── compose.production.yaml
├── Dockerfile
└── requirements.txt
```

## 환경 변수

`.env` 파일이 필요합니다.

환경 변수는 항상 [`.env.example`](/Users/suyeon/AjouUniv/Aolda/ABS/abs-backend/.env.example) 를 기준으로 맞춥니다.  
새 설정을 추가하거나 이름을 바꿀 때는 `.env.example`을 먼저 갱신하고, 필요하면 README 예시도 함께 수정합니다.

```env
DATABASE_URL=mysql+pymysql://user:password@db:3306/abs_db

SESSION_SECRET_KEY=<session-secret>
JWT_SECRET_KEY=<secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080

GOOGLE_CLIENT_ID=<google-client-id>
GOOGLE_CLIENT_SECRET=<google-client-secret>

KEYCLOAK_ISSUER_URI=https://sso.example.com/realms/<realm>
KEYCLOAK_CLIENT_ID=<keycloak-client-id>
KEYCLOAK_CLIENT_SECRET=<keycloak-client-secret>

API_SERVER_URL=https://blog-api.example.com
CONSOLE_PAGE_URL=https://blog.example.com
FRONTEND_URL=https://blog.example.com

S3_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_REGION=auto
S3_ACCESS_KEY_ID=<access-key-id>
S3_SECRET_ACCESS_KEY=<secret-access-key>
S3_BUCKET_NAME=<bucket-name>
S3_PUBLIC_BASE_URL=https://<public-bucket-url>
```

설명:
- `DATABASE_URL`: 애플리케이션이 사용할 DB 연결 문자열
- `SESSION_SECRET_KEY`: 세션 미들웨어 서명 키
- `JWT_SECRET_KEY`: 내부 JWT 서명 키
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth 호환용 클라이언트 설정
- `KEYCLOAK_ISSUER_URI`: Keycloak realm issuer URI
- `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`: Keycloak OIDC 클라이언트 정보
- `API_SERVER_URL`: Keycloak callback URL 생성에 사용할 백엔드 base URL
- `CONSOLE_PAGE_URL`: 로그인 후 기본적으로 돌아갈 프론트 콘솔 URL
- `FRONTEND_URL`: 기본 CORS 허용 대상 프론트 URL
- `S3_*`: Cloudflare R2 등 S3 호환 스토리지 업로드 설정

주의:
- `API_SERVER_URL`에는 origin만 넣어야 합니다.  
  예: `https://backend.localhost`  
  잘못된 예: `https://backend.localhost/api/v1/auth/callback`

## 실행 방법

### 1. 로컬 실행(venv + uvicorn)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Docker Compose 실행

```bash
docker compose -f compose.yaml up -d --build
```

## 기본 정보

- API Base: `http://127.0.0.1:8000/api/v1`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Root: `http://127.0.0.1:8000/`

## 인증 구조

### Keycloak 로그인

인증 흐름은 다음과 같습니다.

1. 프론트가 `GET /api/v1/auth/login` 호출
2. 백엔드가 Keycloak 로그인 페이지로 리다이렉트
3. Keycloak 인증 완료 후 `GET /api/v1/auth/callback`
4. 백엔드가 Keycloak 사용자 정보를 조회
5. `keycloak_sub` 기준으로 기존 사용자 연결 또는 신규 사용자 생성
6. 내부 access token / refresh token 발급
7. 프론트 콘솔의 `/auth/callback` 으로 리다이렉트

### 내부 JWT

백엔드는 Keycloak 토큰을 그대로 프론트에 넘기지 않고, 내부 JWT를 발급합니다.

- access token: API 인증용
- refresh token: 재발급용

토큰 갱신 엔드포인트:
- `POST /api/v1/auth/refresh`

### 다중 콘솔 리다이렉트

OAuth `state`를 이용해 로그인 시작 환경에 따라 적절한 콘솔 URL로 다시 리다이렉트합니다.

예:
- 운영 콘솔에서 로그인 시작 -> 운영 콘솔 `/auth/callback`
- 로컬 콘솔에서 로그인 시작 -> 로컬 콘솔 `/auth/callback`

기본값은 `CONSOLE_PAGE_URL` 입니다.

## 사용자 모델

사용자는 Keycloak 기반으로 관리되며, 주요 필드는 다음과 같습니다.

- `id`
- `username`
- `email`
- `name`
- `bio`
- `avatar`
- `role`
- `keycloak_sub`
- `website`, `github`, `gitlab`, `linkedin`, `discord`, `mail`

특징:
- 기존 사용자 로그인 시 `keycloak_sub`가 연결됩니다.
- 사용자가 직접 수정한 `name`, `avatar`는 로그인할 때 매번 강제로 덮어쓰지 않습니다.
- 작성자 응답에서 프로필 이미지가 없으면 `avatar`는 `null` 입니다.

## 게시글 모델

게시글은 기존 `author_id`를 유지하면서, 별도의 연결 테이블로 공동 편집자를 관리합니다.

관련 구조:
- `posts.author_id`: 기존 대표 작성자
- `post_users`: 게시글과 사용자 간 다대다 연결 테이블

즉 한 게시글에 여러 사용자가 공동 편집자로 연결될 수 있습니다.

## 권한 규칙

### 조회

- 게시글 목록/상세는 비로그인 사용자도 조회 가능
- 비로그인 상태에서는 응답의 `can_edit` 가 항상 `false`

### 수정/삭제

다음 작업은 공동 편집자만 가능합니다.

- 게시글 본문 저장
- 게시글 삭제
- 이미지 업로드
- 이미지 삭제

## 주요 API

### Auth

- `GET /api/v1/auth/login`
- `GET /api/v1/auth/callback`
- `POST /api/v1/auth/refresh`

### Users

- `GET /api/v1/users/me`
- `PUT /api/v1/users/me`
- `GET /api/v1/users/authors`
- `GET /api/v1/users/{username}`

### Posts

- `POST /api/v1/posts`
- `GET /api/v1/posts`
- `GET /api/v1/posts/{post_id}`
- `PUT /api/v1/posts/{post_id}`
- `DELETE /api/v1/posts/{post_id}`
- `POST /api/v1/posts/{post_id}/views`
- `GET /api/v1/posts/{post_id}/views`

### Images

- `POST /api/v1/images/`
- `GET /api/v1/images/posts/{post_id}`
- `DELETE /api/v1/images/{image_id}`

## 게시글 응답 형식

게시글 목록/상세 응답에는 다음 정보가 포함됩니다.

- `id`
- `author_id`
- `authors`
- `can_edit`
- `views`
- `created_at`
- `title`
- `description`
- `tags`
- `image`
- `content` (상세 조회 시)

핵심 필드:

- `authors`: 공동 편집자 username 배열
- `can_edit`: 현재 사용자가 이 글을 수정할 수 있는지 여부

## 게시글 저장 요청 형식

`PUT /api/v1/posts/{post_id}` 요청 body는 다음 필드를 지원합니다.

```json
{
  "title": "제목",
  "description": "설명",
  "tags": ["tag1", "tag2"],
  "image": null,
  "content": "본문",
  "authors": ["alice", "bob"]
}
```

설명:
- `authors`는 선택값입니다.
- 값이 들어오면 공동 편집자 목록을 해당 username 배열로 갱신합니다.
- 존재하지 않는 username이 포함되면 `400 Bad Request` 를 반환합니다.

## 이미지 처리

이미지는 S3 호환 오브젝트 스토리지에 저장됩니다. 현재 기준으로는 Cloudflare R2를 사용할 수 있습니다.

동작:
- 업로드 시 object storage에 파일 저장 후 DB에 공개 URL과 `object_key` 저장
- 게시글별 이미지 목록 조회 가능
- 삭제 시 DB 레코드와 object storage object를 함께 삭제

환경 변수 예시:

```env
S3_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_REGION=auto
S3_ACCESS_KEY_ID=<access-key-id>
S3_SECRET_ACCESS_KEY=<secret-access-key>
S3_BUCKET_NAME=<bucket-name>
S3_PUBLIC_BASE_URL=https://<public-bucket-url>
```

## 조회수 처리

게시글 조회수는 별도 API로 증가합니다.

- `POST /api/v1/posts/{post_id}/views`
- `GET /api/v1/posts/{post_id}/views`

즉 게시글 상세 조회와 조회수 증가가 분리되어 있습니다.

## 마이그레이션

Alembic을 사용합니다.

```bash
alembic upgrade head
alembic downgrade -1
alembic current
```

## 로컬 Keycloak 테스트 메모

로컬 HTTPS 환경에서는 Portless와 같은 도구를 이용해 다음 조합으로 테스트할 수 있습니다.

- 프론트: `https://abs.localhost`
- 백엔드: `https://backend.localhost`

예시:

```env
API_SERVER_URL=https://backend.localhost
CONSOLE_PAGE_URL=https://abs.localhost
```

이 경우 Keycloak client 설정에도 동일한 callback URL이 등록되어 있어야 합니다.

예:
- Valid redirect URI: `https://backend.localhost/api/v1/auth/callback`
- Web origin: `https://abs.localhost`

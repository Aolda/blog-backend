from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str

    # Session / JWT 설정
    SESSION_SECRET_KEY: str
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60분
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일

    # OAuth / OIDC
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # Keycloak OIDC
    KEYCLOAK_ISSUER_URI: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_CLIENT_SECRET: str
    API_SERVER_URL: str = "https://blog-api.aoldacloud.com"
    CONSOLE_PAGE_URL: str = "https://abs.aoldacloud.com"
    FRONTEND_URL: str = "https://blog.aoldacloud.com"

    @property
    def cors_allow_origins(self) -> list[str]:
        console_page_url = self.CONSOLE_PAGE_URL.strip()
        frontend_url = self.FRONTEND_URL.strip()
        return [console_page_url, frontend_url]


    # S3 / R2 object storage
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "auto"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    S3_PUBLIC_BASE_URL: str = ""

settings = Settings()

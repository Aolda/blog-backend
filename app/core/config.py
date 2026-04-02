from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore')

    DATABASE_URL: str

    # JWT 설정
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60분
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7일
    
    # OAuth / OIDC
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # Keycloak OIDC
    KEYCLOAK_ISSUER_URI: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_CLIENT_SECRET: str
    KEYCLOAK_REDIRECT_URI: str = "https://blog-api.aoldacloud.com/api/v1/auth/callback"
    FRONTEND_URL: str = "https://blog.aoldacloud.com"

settings = Settings()

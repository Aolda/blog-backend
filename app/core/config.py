from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 파일을 읽어오도록 설정
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore')

    # 형식: "mysql+pymysql://<사용자>:<비밀번호>@<호스트>:<포트>/<DB이름>"
    DATABASE_URL: str

    # JWT 설정
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60분
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7일
    
    # Google Auth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

# 설정 객체 인스턴스 생성
settings = Settings()
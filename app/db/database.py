from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings # config.py의 db url 가져옴

# 데이터베이스 엔진 생성
# connect_args: PyMySQL 사용 시 발생할 수 있는 오류 방지
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"charset": "utf8mb4"},
    echo=True
)

# 데이터베이스 세션 생성
# bind=engine: 이 세션이 사용할 엔진을 지정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 모델 클래스
Base = declarative_base()

# 의존성 주입을 위한 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
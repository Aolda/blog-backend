import mimetypes
from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from app.core.config import settings


def _require_storage_settings() -> None:
    required = {
        "S3_ENDPOINT_URL": settings.S3_ENDPOINT_URL,
        "S3_ACCESS_KEY_ID": settings.S3_ACCESS_KEY_ID,
        "S3_SECRET_ACCESS_KEY": settings.S3_SECRET_ACCESS_KEY,
        "S3_BUCKET_NAME": settings.S3_BUCKET_NAME,
        "S3_PUBLIC_BASE_URL": settings.S3_PUBLIC_BASE_URL,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"오브젝트 스토리지 설정이 누락되었습니다: {', '.join(missing)}",
        )


@lru_cache(maxsize=1)
def get_s3_client():
    _require_storage_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    )


def build_public_url(object_key: str) -> str:
    _require_storage_settings()
    return f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{object_key.lstrip('/')}"


def upload_object(object_key: str, content: bytes, content_type: str | None = None) -> str:
    client = get_s3_client()
    guessed_content_type = content_type or mimetypes.guess_type(object_key)[0] or "application/octet-stream"

    try:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=object_key,
            Body=content,
            ContentType=guessed_content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=500, detail=f"오브젝트 스토리지 업로드 실패: {exc}") from exc

    return build_public_url(object_key)


def delete_object(object_key: str) -> None:
    client = get_s3_client()
    try:
        client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=object_key)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=500, detail=f"오브젝트 스토리지 삭제 실패: {exc}") from exc

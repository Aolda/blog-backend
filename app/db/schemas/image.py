from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageUploadResponse(BaseModel):
    id: int
    post_id: int
    url: str


class ImageResponse(BaseModel):
    id: int
    post_id: int
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

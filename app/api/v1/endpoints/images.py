import os
import uuid
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Image as ImageModel, Post as PostModel, User as UserModel
from app.db.schemas.image import ImageResponse, ImageUploadResponse

router = APIRouter()

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    request: Request,
    post_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    이미지 업로드 API
    - 파일을 받아 서버에 저장하고 post_id와 함께 DB에 저장.
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글에만 이미지를 업로드할 수 있습니다.")

    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception:
        raise HTTPException(status_code=500, detail="이미지 저장 중 오류가 발생했습니다.")

    file_url = f"{request.base_url}uploads/{filename}"
    image = ImageModel(post_id=post_id, url=file_url)
    db.add(image)
    db.commit()
    db.refresh(image)

    return ImageUploadResponse(id=image.id, post_id=image.post_id, url=image.url)


@router.get("/posts/{post_id}", response_model=List[ImageResponse])
def list_images_by_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """
    게시글 기준 이미지 목록 조회 API
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    images = (
        db.query(ImageModel)
        .filter(ImageModel.post_id == post_id)
        .order_by(ImageModel.created_at.asc())
        .all()
    )
    return images


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    이미지 삭제 API
    - DB + uploads 파일을 함께 삭제.
    """
    image = db.query(ImageModel).filter(ImageModel.id == image_id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지를 찾을 수 없습니다."
        )

    post = db.query(PostModel).filter(PostModel.id == image.post_id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인 게시글의 이미지만 삭제할 수 있습니다."
        )

    filename = os.path.basename(image.url)
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(image)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

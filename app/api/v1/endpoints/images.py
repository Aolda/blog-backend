import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Image as ImageModel, Post as PostModel, User as UserModel
from app.db.schemas.image import ImageResponse, ImageUploadResponse
from app.services.object_storage import delete_object, upload_object

router = APIRouter()


def can_edit_post(post: PostModel, current_user: UserModel) -> bool:
    if any(user.id == current_user.id for user in post.users):
        return True
    return post.author_id == current_user.id


@router.post("/", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    post_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    이미지 업로드 API
    - 파일을 받아 S3 호환 스토리지(R2 등)에 저장하고 post_id와 함께 DB에 저장.
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if not can_edit_post(post, current_user):
        raise HTTPException(status_code=403, detail="공동 편집자만 이미지를 업로드할 수 있습니다.")

    extension = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4()}{extension}"
    object_key = f"posts/{post_id}/{filename}"

    try:
        content = await file.read()
        file_url = upload_object(object_key, content, file.content_type)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"이미지 저장 중 오류가 발생했습니다: {exc}") from exc

    image = ImageModel(post_id=post_id, url=file_url, object_key=object_key)
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
    - DB와 오브젝트 스토리지를 함께 정리합니다.
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
    if not can_edit_post(post, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="공동 편집자만 이미지를 삭제할 수 있습니다."
        )

    if not image.object_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 오브젝트 키가 없습니다."
        )

    delete_object(image.object_key)

    db.delete(image)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

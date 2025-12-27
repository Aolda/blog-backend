from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db.models import Post as PostModel, User as UserModel
from app.db.schemas.post import Post as PostSchema
from app.api.deps import get_current_admin

router = APIRouter()

@router.get("/posts", response_model=List[PostSchema])
def read_all_posts_admin(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    """
    [관리자] 전체 게시글 조회
    """
    posts = (
        db.query(PostModel)
        .options(joinedload(PostModel.author))
        .options(joinedload(PostModel.category))
        .order_by(PostModel.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return posts

@router.delete("/posts/{post_id}", status_code=204)
def delete_post_admin(
    post_id: int,
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    """
    [관리자] 게시글 강제 삭제
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
    db.delete(post)
    db.commit()
    return None

@router.patch("/posts/{post_id}/state", response_model=PostSchema)
def update_post_state_admin(
    post_id: int,
    status_in: str,
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    """
    [관리자] 게시글 상태 변경
    - published <-> hidden으로 상태를 강제 변경합니다.
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
    post.status = status_in
    db.commit()
    db.refresh(post)
    return post
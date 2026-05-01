from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from app.db.models import Post as PostModel, User as UserModel
from app.db.schemas.post import (
    PaginatedPostsResponse,
    PostContentUpdate,
    PostResponse,
    PostSummaryResponse,
    PostTemplateResponse,
)
from app.api.deps import get_db, get_current_user, get_optional_current_user

router = APIRouter()


def can_edit_post(post: PostModel, current_user: UserModel) -> bool:
    if any(user.id == current_user.id for user in post.users):
        return True
    return post.author_id == current_user.id


def get_post_author_names(post: PostModel) -> List[str]:
    usernames = [user.username for user in post.users if user.username]
    if usernames:
        return sorted(set(usernames))
    if post.author and post.author.username:
        return [post.author.username]
    return []


def serialize_post(
    post: PostModel,
    include_content: bool,
    current_user: UserModel | None = None,
) -> dict:
    author_names = get_post_author_names(post)
    payload = {
        "id": post.id,
        "author_id": post.author_id,
        "authors": author_names,
        "can_edit": bool(current_user and can_edit_post(post, current_user)),
        "views": post.views or 0,
        "created_at": post.created_at,
        "title": post.title,
        "description": post.description,
        "tags": post.tags or [],
        "image": post.image,
    }
    if include_content:
        payload["content"] = post.content
    return payload


@router.post("", response_model=PostTemplateResponse)
def create_post(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # 로그인 필수
):
    """
    게시글 생성 API
    - DB에 빈 게시글 레코드를 만들고 post_id를 발급합니다.
    """
    
    # db에 ID 발급용 레코드 생성
    new_post = PostModel(
        author_id=current_user.id,
        views=0,
        users=[current_user],
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return PostTemplateResponse(post_id=new_post.id)

@router.get("", response_model=PaginatedPostsResponse)
def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel | None = Depends(get_optional_current_user),
):
    """
    게시글 목록 조회 API
    """
    skip = (page - 1) * limit
    query = (
        db.query(PostModel)
        .options(joinedload(PostModel.author), joinedload(PostModel.users))
        .order_by(PostModel.created_at.desc())
    )
    total = query.count()
    posts = query.offset(skip).limit(limit).all()
    return PaginatedPostsResponse(
        items=[serialize_post(post, include_content=False, current_user=current_user) for post in posts],
        page=page,
        limit=limit,
        total=total,
    )

@router.get("/{post_id}", response_model=PostResponse)
def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel | None = Depends(get_optional_current_user),
):
    """
    게시글 상세 조회 API
    """
    post = (
        db.query(PostModel)
        .options(joinedload(PostModel.author), joinedload(PostModel.users))
        .filter(PostModel.id == post_id)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return serialize_post(post, include_content=True, current_user=current_user)

@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_in: PostContentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    게시글 수정 API
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if not can_edit_post(post, current_user):
        raise HTTPException(status_code=403, detail="공동 편집자만 게시글을 수정할 수 있습니다.")

    post.title = post_in.title
    post.description = post_in.description
    post.tags = post_in.tags
    post.image = post_in.image
    post.content = post_in.content
    if post_in.authors is not None:
        author_usernames = list(dict.fromkeys(post_in.authors))
        authors = (
            db.query(UserModel)
            .filter(UserModel.username.in_(author_usernames))
            .all()
        )
        found_usernames = {user.username for user in authors}
        missing_usernames = [
            username for username in author_usernames if username not in found_usernames
        ]
        if missing_usernames:
            raise HTTPException(
                status_code=400,
                detail=f"존재하지 않는 작성자입니다: {', '.join(missing_usernames)}",
            )
        post.users = authors

    db.add(post)
    db.commit()
    db.refresh(post)
    post = (
        db.query(PostModel)
        .options(joinedload(PostModel.author), joinedload(PostModel.users))
        .filter(PostModel.id == post_id)
        .first()
    )
    return serialize_post(post, include_content=True, current_user=current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    게시글 삭제 API
    - 공동 편집자만 삭제 가능.
    """
    post = (
        db.query(PostModel)
        .options(joinedload(PostModel.users))
        .filter(PostModel.id == post_id)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if not can_edit_post(post, current_user):
        raise HTTPException(status_code=403, detail="공동 편집자만 게시글을 삭제할 수 있습니다.")

    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{post_id}/views")
def increase_view_count(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    게시글 조회수 증가 API
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
    post.views += 1

    db.add(post)
    db.commit()
    
    db.refresh(post)
    
    return {"views": post.views}

@router.get("/{post_id}/views")
def get_view_count(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    게시글 조회수 조회 API
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    return {"views": post.views}

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Post as PostModel, User as UserModel
from app.db.schemas.post import PostCreate, Post as PostSchema, PostUpdate
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=PostSchema, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # 로그인 필수
):
    """
    게시글 작성 API
    - 로그인한 사용자만 작성할 수 있습니다.
    - 작성자는 현재 로그인한 사용자로 자동 설정됩니다.
    """
    
    # author_id에 로그인한 사용자의 ID(current_user.id)를 넣음
    new_post = PostModel(
        **post_in.model_dump(),
        author_id=current_user.id 
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post) # 생성된 ID, 시간 정보 등을 DB에서 다시 읽어옴
    
    return new_post

@router.get("/", response_model=List[PostSchema])
def read_posts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    게시글 목록 조회 API
    - skip: 앞의 N개를 건너뜁니다.
    - limit: 최대 N개를 가져옵니다.
    - 작성일 역순(최신순)으로 정렬하여 반환합니다.
    """
    posts = (
        db.query(PostModel)
        .order_by(PostModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
        )
    
    return posts

@router.get("/{post_id}", response_model=PostSchema)
def read_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    게시글 상세 조회 API
    - post_id에 해당하는 게시글 하나를 가져옵니다.
    - 게시글이 없으면 오류를 반환합니다.
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    return post

@router.put("/{post_id}", response_model=PostSchema)
def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # 로그인 필수
):
    """
    게시글 수정 API
    - 작성자 본인만 수정할 수 있습니다.
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    # 내 아이디(current_user.id)와 글 작성자 아이디(post.author_id)가 다르면 거부
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="수정 권한이 없습니다."
        )
        
    # 수정한 데이터만 골라서 업데이트
    update_data = post_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(post, field, value) # post.field = value
        
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # 로그인 필수
):
    """
    게시글 삭제 API
    - 작성자 본인만 삭제할 수 있습니다.
    """

    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="삭제 권한이 없습니다."
        )
        
    db.delete(post)
    db.commit()
    
    return None
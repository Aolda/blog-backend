from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import Post as PostModel, User as UserModel
from app.db.schemas.post import PostTemplateResponse
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.post("/template", response_model=PostTemplateResponse)
def create_post_template(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # 로그인 필수
):
    """
    MDX 작성용 템플릿 API
    - db에 빈 레코드 만들고 post_id 발급
    - 프론트에서 MDX 파일 만들 때 필요한 메타데이터를 JSON으로 반환
    """
    
    # db에 ID 발급용 레코드 생성
    new_post = PostModel(
        author_id=current_user.id,
        views=0
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    date_str = new_post.created_at.strftime("%Y-%m-%d")
    
    frontmatter_example = f"""---
title: ""
date: "{date_str}"
id: {new_post.id}
author: "{current_user.username}"
---"""
    
    return PostTemplateResponse(
        post_id=new_post.id,
        author_name=current_user.username,
        created_at=date_str,
        frontmatter_example=frontmatter_example
    )

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


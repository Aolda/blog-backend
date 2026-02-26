from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import Post as PostModel, User as UserModel
from app.db.schemas.post import (
    PostContentUpdate,
    PostResponse,
    PostSummaryResponse,
    PostTemplateResponse,
)
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
title: ''
description: ''
date: {date_str}
tags: []
image: ''
author: ['{current_user.username}']
---
"""
    
    return PostTemplateResponse(
        post_id=new_post.id,
        author_name=current_user.username,
        created_at=date_str,
        frontmatter_example=frontmatter_example
    )

@router.get("", response_model=List[PostSummaryResponse])
def list_posts(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    게시글 목록 조회 API
    """
    skip = (page - 1) * limit
    posts = (
        db.query(PostModel)
        .order_by(PostModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return posts

@router.get("/{post_id}", response_model=PostResponse)
def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    게시글 상세 조회 API
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post

@router.put("/{post_id}/content", response_model=PostResponse)
def update_post_content(
    post_id: int,
    post_in: PostContentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    게시글 본문 저장 API
    """
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 게시글만 수정할 수 있습니다.")

    post.content = post_in.content
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

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

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from app.db.models import Post as PostModel, User as UserModel
from app.db.schemas.post import (
    PostContentUpdate,
    PostFrontmatter,
    PostResponse,
    PostSummaryResponse,
    PostTemplateResponse,
)
from app.api.deps import get_db, get_current_user

router = APIRouter()


def build_frontmatter(post: PostModel, author_name: str) -> PostFrontmatter:
    date_str = post.created_at.strftime("%Y-%m-%d")
    return PostFrontmatter(
        title=post.title or "",
        description=post.description or "",
        date=date_str,
        tags=post.tags or [],
        image=post.image or "",
        author=[author_name],
    )


def build_frontmatter_header(frontmatter: PostFrontmatter) -> str:
    tags_text = ", ".join([f"'{tag}'" for tag in frontmatter.tags])
    author_text = ", ".join([f"'{author}'" for author in frontmatter.author])
    return (
        "---\n"
        f"title: '{frontmatter.title}'\n"
        f"description: '{frontmatter.description}'\n"
        f"date: {frontmatter.date}\n"
        f"tags: [{tags_text}]\n"
        f"image: '{frontmatter.image}'\n"
        f"author: [{author_text}]\n"
        "---"
    )


def serialize_post(post: PostModel, include_content: bool) -> dict:
    author_name = post.author.username if post.author else ""
    frontmatter = build_frontmatter(post, author_name)
    payload = {
        "id": post.id,
        "author_id": post.author_id,
        "views": post.views or 0,
        "created_at": post.created_at,
        "title": post.title,
        "description": post.description,
        "tags": post.tags or [],
        "image": post.image,
        "frontmatter": frontmatter,
        "frontmatter_header": build_frontmatter_header(frontmatter),
    }
    if include_content:
        payload["content"] = post.content
    return payload


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
    
    frontmatter_example = (
        "---\n"
        "title: ''\n"
        "description: ''\n"
        f"date: {date_str}\n"
        "tags: []\n"
        "image: ''\n"
        f"author: ['{current_user.username}']\n"
        "---\n"
    )
    
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
        .options(joinedload(PostModel.author))
        .order_by(PostModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [serialize_post(post, include_content=False) for post in posts]

@router.get("/{post_id}", response_model=PostResponse)
def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    게시글 상세 조회 API
    """
    post = (
        db.query(PostModel)
        .options(joinedload(PostModel.author))
        .filter(PostModel.id == post_id)
        .first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return serialize_post(post, include_content=True)

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

    post.title = post_in.title
    post.description = post_in.description
    post.tags = post_in.tags
    post.image = post_in.image
    post.content = post_in.content
    db.add(post)
    db.commit()
    db.refresh(post)
    post = (
        db.query(PostModel)
        .options(joinedload(PostModel.author))
        .filter(PostModel.id == post_id)
        .first()
    )
    return serialize_post(post, include_content=True)

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

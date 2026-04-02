from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
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


def build_frontmatter(post: PostModel, author_names: List[str]) -> PostFrontmatter:
    date_str = post.created_at.strftime("%Y-%m-%d")
    return PostFrontmatter(
        title=post.title or "",
        description=post.description or "",
        date=date_str,
        tags=post.tags or [],
        image=post.image or "",
        author=author_names,
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


def serialize_post(
    post: PostModel,
    include_content: bool,
    current_user: UserModel | None = None,
) -> dict:
    author_names = get_post_author_names(post)
    frontmatter = build_frontmatter(post, author_names)
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
        views=0,
        users=[current_user],
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
        author_names=[current_user.username],
        created_at=date_str,
        frontmatter_example=frontmatter_example
    )

@router.get("", response_model=List[PostSummaryResponse])
def list_posts(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: UserModel | None = Depends(get_optional_current_user),
):
    """
    게시글 목록 조회 API
    """
    skip = (page - 1) * limit
    posts = (
        db.query(PostModel)
        .options(joinedload(PostModel.author), joinedload(PostModel.users))
        .order_by(PostModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [serialize_post(post, include_content=False, current_user=current_user) for post in posts]

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

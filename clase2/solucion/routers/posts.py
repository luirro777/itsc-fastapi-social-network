from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select

from dependencies import CurrentUser, SessionDep, get_post_or_404, is_admin, require
from models import Post, PostCreate, PostPublic, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostPublic])
def read_posts(db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20):
    stmt = select(Post).order_by(col(Post.created_at).desc()).offset(offset).limit(limit)
    return db.exec(stmt).all()


@router.get("/{post_id}", response_model=PostPublic)
def read_post(post_id: int, db: SessionDep):
    return get_post_or_404(db, post_id)


@router.post("", response_model=PostPublic, status_code=201)
def create_post(data: PostCreate, db: SessionDep, current_user: CurrentUser):    
    post = Post(**data.model_dump(), author_id= current_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.patch("/{post_id}", response_model=PostPublic)
def update_post(post_id: int, data: PostUpdate, db: SessionDep, current_user: CurrentUser):    
    post = get_post_or_404(db, post_id)
    require(post.author_id == current_user.id or is_admin(current_user))
    post.sqlmodel_update(data.model_dump(exclude_unset=True))
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: SessionDep, current_user: CurrentUser):    
    post = get_post_or_404(db, post_id)
    require(post.author_id == current_user.id or is_admin(current_user))
    db.delete(post)
    db.commit()

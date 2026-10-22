from fastapi import APIRouter

from dependencies import SessionDep, get_user_or_404
from models import PostPublic, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserPublic)
def read_user(user_id: int, db: SessionDep):
    return get_user_or_404(db, user_id)


@router.get("/{user_id}/posts", response_model=list[PostPublic])
def read_user_posts(user_id: int, db: SessionDep):
    return get_user_or_404(db, user_id).posts

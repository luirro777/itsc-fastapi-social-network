from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select
from models import Like, Post

from dependencies import SessionDep, get_user_or_404
from models import PostPublic, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserPublic)
def read_user(user_id: int, db: SessionDep):
    return get_user_or_404(db, user_id)


@router.get("/{user_id}/posts", response_model=list[PostPublic])
def read_user_posts(user_id: int, db: SessionDep):
    return get_user_or_404(db, user_id).posts


@router.get("/{user_id}/likes", response_model=list[PostPublic])
def read_user_likes(
    user_id: int, db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20
):
    """Los posts a los que este usuario le dio like (el más reciente primero)."""
    # TODO 6 (DESAFÍO, sin pistas de código): es el espejo del TODO 5.
    #   Allá: de un post → sus usuarios.   Acá: de un usuario → sus posts.
    #   Necesitas select(Post), un join con Like, y filtrar por Like.user_id.
    #   Recuerda: 404 si el usuario no existe, y orden/paginación como en los otros listados.
    #   (Agrega a los imports de arriba lo que necesites: Like, Post.)
    #raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 6: posts que le gustaron")
    get_user_or_404(db, user_id)
    stmt = (
        select(Post)
        .join(Like, col(Like.post_id) == col(Post.id))
        .where(Like.user_id == user_id)
        .order_by(col(Like.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    return db.exec(stmt).all()

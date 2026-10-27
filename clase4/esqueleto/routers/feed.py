"""El feed: los posts de las personas a las que sigo."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from dependencies import CurrentUser, SessionDep
from models import PostWithLikes

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=list[PostWithLikes])
def read_feed(
    db: SessionDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 20,
):
    # TODO 7: los posts de las personas a las que sigo, más nuevos primero, con likes_count.
    #   PASO 1 — hazlo como se te ocurra (aunque sea con un `for` que consulte seguido por seguido).
    #            Confirma con Swagger que funciona.
    #   PASO 2 — córrele los tests: test_feed_query_count_does_not_grow_with_followed_users cuenta las
    #            consultas SQL. Si tu `for` hace una consulta por seguido, falla (eso es el problema N+1).
    #   PASO 3 — reemplázalo por UNA consulta con subquery:
    #       from sqlmodel import col, select
    #       from models import Follow, Post
    #       from routers.posts import posts_with_likes, to_post_with_likes   # ¡reutilizamos la clase 3!
    #
    #       followed_ids = select(Follow.followed_id).where(Follow.follower_id == current_user.id)
    #       stmt = (
    #           posts_with_likes()
    #           .where(col(Post.author_id).in_(followed_ids))
    #           .order_by(col(Post.created_at).desc())
    #           .offset(offset).limit(limit)
    #       )
    #       return [to_post_with_likes(row) for row in db.exec(stmt).all()]
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 7: feed")

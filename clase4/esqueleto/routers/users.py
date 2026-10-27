from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select

from dependencies import CurrentUser, SessionDep, get_user_or_404
from models import Like, Post, PostPublic, UserProfile, UserPublic

# TODO 1 (cont.): cuando tengas la tabla Follow, agrégala al import de models de arriba
#                 (y también `User`, `func` de sqlalchemy y `Session` de sqlmodel cuando los pidan).

router = APIRouter(prefix="/users", tags=["users"])


# ═══════════════ Perfil con contadores ═══════════════
# TODO 2: GET /users/{id} hoy devuelve UserPublic. Queremos UserProfile (followers_count y following_count).
#   Escribe esta función auxiliar:
#
#   def to_profile(db: Session, user: User) -> UserProfile:
#       followers = db.exec(
#           select(func.count()).select_from(Follow).where(Follow.followed_id == user.id)
#       ).one()
#       following = db.exec(
#           select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
#       ).one()
#       return UserProfile.model_validate(
#           user, update={"followers_count": followers, "following_count": following}
#       )
#
#   Y úsala en read_user (cambia también el response_model a UserProfile).
#   Pregunta: los dos conteos son casi idénticos. ¿Qué columna cambia y por qué?
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


# ═══════════════ Seguir / dejar de seguir ═══════════════
@router.put("/{user_id}/follow", response_model=UserProfile)
def follow_user(user_id: int, db: SessionDep, current_user: CurrentUser):
    # TODO 3: seguir a un usuario (idempotente, igual que el like).
    #   a) target = get_user_or_404(db, user_id)
    #   b) si target.id == current_user.id → 400 (status.HTTP_400_BAD_REQUEST) "No puedes seguirte a ti mismo"
    #   c) si db.get(Follow, (current_user.id, user_id)) es None:
    #          db.add(Follow(follower_id=current_user.id, followed_id=user_id)); db.commit()
    #      (el orden de la tupla es el de las primary_key: follower, followed)
    #   d) return to_profile(db, target)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 3: seguir")


@router.delete("/{user_id}/follow", response_model=UserProfile)
def unfollow_user(user_id: int, db: SessionDep, current_user: CurrentUser):
    # TODO 4: dejar de seguir. Misma idea al revés, y también idempotente.
    #   a) target = get_user_or_404   b) follow = db.get(Follow, (current_user.id, user_id))
    #   c) si follow existe: db.delete(follow) y db.commit()   d) return to_profile(db, target)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 4: dejar de seguir")


# ═══════════════ Listas: followers vs following ═══════════════
# Follow tiene DOS claves foráneas hacia users, así que el JOIN necesita la condición explícita.
# Prueba  select(User).join(Follow)  sin condición y lee el error: ¿qué te está pidiendo SQLAlchemy?
#   followers de X = usuarios que lo SIGUEN   → los follower_id de las filas donde followed_id == X
#   following de X = usuarios a los que SIGUE → los followed_id de las filas donde follower_id == X
@router.get("/{user_id}/followers", response_model=list[UserPublic])
def read_followers(
    user_id: int, db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20
):
    # TODO 5: quiénes siguen a user_id.
    #   get_user_or_404(db, user_id)
    #   stmt = (
    #       select(User)
    #       .join(Follow, col(Follow.follower_id) == col(User.id))
    #       .where(Follow.followed_id == user_id)
    #       .order_by(col(Follow.created_at).desc())
    #       .offset(offset).limit(limit)
    #   )
    #   return db.exec(stmt).all()
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 5: followers")


@router.get("/{user_id}/following", response_model=list[UserPublic])
def read_following(
    user_id: int, db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20
):
    # TODO 6 (DESAFÍO, sin código): es el espejo del TODO 5, con las columnas INVERTIDAS.
    #   Dibuja en el pizarrón dos filas de la tabla follows y decide cuál columna va en el join
    #   y cuál en el where. Este es el error que más se comete en esta clase.
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 6: following")

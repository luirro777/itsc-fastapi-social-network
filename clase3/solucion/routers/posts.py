from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, select, func

from dependencies import CurrentUser, SessionDep, get_post_or_404, is_admin, require
from models import Post, PostCreate, PostPublic, PostUpdate, PostWithLikes, UserPublic, Like, User

# TODO 1 (cont.): cuando tengas la tabla Like, agrégala al import de models de arriba
#                 (y también `User`, `func` de sqlmodel y `Session` de sqlmodel cuando los pidan).

router = APIRouter(prefix="/posts", tags=["posts"])


# ═══════════════ Lectura de posts CON la cuenta de likes ═══════════════
# TODO 2: hoy GET /posts devuelve PostPublic (sin likes). Queremos PostWithLikes.
#   Escribe estas tres funciones auxiliares:
#
def posts_with_likes():
    """SELECT posts.*, COUNT(likes.user_id)
        FROM posts LEFT JOIN likes ON likes.post_id = posts.id
        GROUP BY posts.id"""
    return (
          select(Post, func.count(col(Like.user_id)))
          .join(Like, col(Like.post_id) == col(Post.id), isouter=True)
          .group_by(col(Post.id))
    )

def to_post_with_likes(row) -> PostWithLikes:
    post, likes_count = row        # cada fila es una tupla (Post, int)
    return PostWithLikes.model_validate(post, update={"likes_count": likes_count})

def get_post_with_likes_or_404(db: Session, post_id: int) -> PostWithLikes:
    row = db.exec(posts_with_likes().where(Post.id == post_id)).first()
    #   → si row es None: 404 "Post no encontrado"; si no: return to_post_with_likes(row)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post no encontrado")
    return to_post_with_likes(row)
#
#   Y úsalas en los dos GET de abajo (cambia también el response_model).
#   Pregunta: ¿por qué isouter=True? Prueba quitarlo y mira qué pasa con un post sin likes.
@router.get("", response_model=list[PostWithLikes])
def read_posts(db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20):
    #stmt = select(Post).order_by(col(Post.created_at).desc()).offset(offset).limit(limit)
    stmt = posts_with_likes().order_by(col(Post.created_at).desc()).offset(offset).limit(limit)
    return [to_post_with_likes(row) for row in db.exec(stmt).all()]


@router.get("/{post_id}", response_model=PostWithLikes)
def read_post(post_id: int, db: SessionDep):
    return get_post_with_likes_or_404(db, post_id)


# ═══════════════ CRUD de la clase 2 (sin cambios) ═══════════════
@router.post("", response_model=PostPublic, status_code=201)
def create_post(data: PostCreate, db: SessionDep, current_user: CurrentUser):
    post = Post(**data.model_dump(), author_id=current_user.id)
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
    db.delete(post)  # ¿qué pasa con los likes de este post? (mira el TODO 1 y el TODO 8)
    db.commit()


# ═══════════════ Likes ═══════════════
@router.put("/{post_id}/like", response_model=PostWithLikes)
def like_post(post_id: int, db: SessionDep, current_user: CurrentUser):
    # TODO 3: dar like. PUT = "déjalo en este estado": hacerlo dos veces NO es un error (idempotente).
    #   a) get_post_or_404(db, post_id)
    #   b) like = db.get(Like, (current_user.id, post_id))
    #      → get con clave COMPUESTA: la tupla va en el orden de las primary_key del modelo
    #   c) si like es None: db.add(Like(user_id=current_user.id, post_id=post_id)) y db.commit()
    #      (si ya existía, no hagas nada)
    #   d) return get_post_with_likes_or_404(db, post_id)     → el cliente ve el conteo nuevo
    #raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 3: dar like")
    get_post_or_404(db, post_id)
    like = db.get(Like, current_user.id, post_id)
    if like is None:
        db.add(like)
        db.commit()
    return get_post_with_likes_or_404(db, post_id)


@router.delete("/{post_id}/like", response_model=PostWithLikes)
def unlike_post(post_id: int, db: SessionDep, current_user: CurrentUser):
    # TODO 4: quitar like. Misma idea, al revés, y también idempotente.
    #   a) get_post_or_404   b) like = db.get(Like, (current_user.id, post_id))
    #   c) si like existe: db.delete(like) y db.commit()
    #   d) return get_post_with_likes_or_404(db, post_id)
    #raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 4: quitar like")
    get_post_or_404(db, post_id)
    like = db.get(Like, (current_user.id, post_id))
    if like is not None:
        db.delete(like)
        db.commit()
    return get_post_with_likes_or_404(db, post_id)


@router.get("/{post_id}/likes", response_model=list[UserPublic])
def read_post_likes(
    post_id: int, db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20
):
    """¿Quiénes le dieron like a este post? (los más recientes primero)"""
    # TODO 5: devuelve los USUARIOS que dieron like (no los likes). Es un JOIN:
    #   get_post_or_404(db, post_id)
    #   stmt = (
    #       select(User)
    #       .join(Like, col(Like.user_id) == col(User.id))
    #       .where(Like.post_id == post_id)
    #       .order_by(col(Like.created_at).desc())
    #       .offset(offset).limit(limit)
    #   )
    #   return db.exec(stmt).all()
    #raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 5: quiénes dieron like")
    get_post_or_404(db, post_id)
    stmt = (
        select(User)
        .join(Like, col(Like.user_id) == col(User.id))
        .where(Like.post_id == post_id)
        .order_by(col(Like.created_at).desc())
        .offset(offset)
        .limit(limit)        
    )
    db.exec(stmt).all()

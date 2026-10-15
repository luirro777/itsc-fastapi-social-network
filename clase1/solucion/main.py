"""CLASE 1 — ESQUELETO: una API que guarda datos (FastAPI + SQLModel + SQLite).

Ejecutar:   uv run fastapi dev clase1/esqueleto/main.py      →   http://127.0.0.1:8000/docs
Los endpoints sin terminar responden 501 ("no implementado"): así los ves en /docs
desde el principio y la app siempre arranca. Busca los  # TODO n  y ve en orden.
Si cambias las tablas, borra clase1.db (create_all NO modifica tablas existentes).
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════ Base de datos (ya resuelta, no la toques hoy) ═══════════════
engine = create_engine("sqlite:///./clase1.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(engine)  # crea las tablas que no existan
    yield


app = FastAPI(title="Clase 1", lifespan=lifespan)


# ═══════════════ PARTE 1: de HTTP a FastAPI ═══════════════
@app.get("/saludo/{nombre}")
def saludo(nombre: str, mayusculas: bool = False):
    """nombre → parámetro de RUTA · mayusculas → parámetro de QUERY (?mayusculas=true).
    Pruébalo en /docs y fíjate en qué se manda dónde."""
    texto = f"Hola, {nombre}!"
    return {"mensaje": texto.upper() if mayusculas else texto}


# TODO 1: crea  GET /suma  que reciba dos enteros por query (a y b) y devuelva
#         {"resultado": a + b}.
#         Prueba /suma?a=1&b=2  y luego  /suma?a=1&b=hola  → ¿qué código obtienes y por qué?
@app.get("/suma")
def suma(a: int, b: int):
    return {"resultado": a + b}


# ═══════════════ PARTE 2: la tabla Post y su CRUD ═══════════════
#═══════════════ PARTE 3: tablas vs. schemas ═══════════════
# TODO 6: separa "lo que se guarda" de "lo que entra y sale".
#   1) Clase base con los campos comunes:     class PostBase(SQLModel): title, content
#   2) La tabla hereda de la base:            class Post(PostBase, table=True): id, created_at
#   3) Schemas SIN table=True:
#        PostCreate(PostBase)        → lo que ENTRA al crear (sin id ni created_at)
#        PostUpdate(SQLModel)        → title y content opcionales (PATCH parcial)
#        PostPublic(PostBase)        → lo que SALE: PostBase + id + created_at
#   4) Cambia las firmas de los endpoints: body → PostCreate / PostUpdate,
#      response_model → PostPublic.
#   Pistas: Post.model_validate(data) convierte un PostCreate en tabla ·
#           data.model_dump(exclude_unset=True) devuelve solo lo que el cliente envió.
#   Repite la prueba del id 999: ahora debe ignorarse.

# ═══════════════ PARTE 4: usuarios y relación 1:N ═══════════════
# TODO 7:
#   1) Tabla User (__tablename__ = "users"): id, username (3-50 caracteres, único).
#   2) Post.author_id: int = Field(foreign_key="users.id")
#   3) Relación en ambos lados:
#        User.posts:  list["Post"] = Relationship(back_populates="author")
#        Post.author: User = Relationship(back_populates="posts")
#   4) Schemas UserCreate (username) y UserPublic (id + username).
#      PostCreate gana author_id (TEMPORAL: lo mandamos a mano; en la clase 2 sale del token).
#   5) Endpoints:  POST /users (409 si el username existe) · GET /users/{user_id} (404) ·
#                  GET /users/{user_id}/posts  → devuelve user.posts
#      Y en create_post: si el autor no existe → 404.
#   Borra clase1.db antes de reiniciar.

# --- Schemas y Tabla de Usuarios ---
class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=50)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, max_length=50, unique=True, index=True)

    posts: list["Post"] = Relationship(back_populates="author")


class UserCreate(UserBase):
    pass


class UserPublic(UserBase):
    id: int


class PostBase(SQLModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)


class Post(PostBase, table=True):  # table=True → esta clase ES una tabla
    __tablename__ = "posts"

    id: int | None = Field(default=None, primary_key=True)       
    created_at: datetime = Field(default_factory=utcnow)
    author_id: int = Field(foreign_key="users.id")

    author: User | None = Relationship(back_populates="posts")

class PostCreate(PostBase):
    """Lo que ENTRA al crear (solo title y content). Ignora si mandan id o created_at."""
    author_id: int

class PostUpdate(SQLModel):
    """Para PATCH parcial: title y content son opcionales."""
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1, max_length=2000)

class PostPublic(PostBase):
    """Lo que SALE al cliente: PostBase + id + created_at."""
    id: int
    created_at: datetime
    author_id: int


# ═══════════════ PARTE 4: Endpoints de Usuarios ═══════════════
# TODO 7:
#  - POST /users (409 si el username existe)
#  - GET /users/{user_id} (404 si no existe)
#  - GET /users/{user_id}/posts → devuelve user.posts
@app.post("/users", response_model=UserPublic, status_code=201)
def create_user(user_in: UserCreate, db: SessionDep) -> User:
    existing_user = db.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=409, detail="El nombre de usuario ya existe"
        )

    db_user = User.model_validate(user_in)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, db: SessionDep) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@app.get("/users/{user_id}/posts", response_model=list[PostPublic])
def read_user_posts(user_id: int, db: SessionDep) -> list[Post]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user.posts


# ═══════════════ PARTES 2, 3 y 4: Endpoints de Posts ═══════════════
# TODO 3 & 7: Validar autor existente y crear post
@app.post("/posts", response_model=PostPublic, status_code=201)
def create_post(post_in: PostCreate, db: SessionDep) -> Post:
    author = db.get(User, post_in.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="El autor especificado no existe")

    db_post = Post.model_validate(post_in)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


# TODO 4: Listar (con paginación limit/offset) y obtener un post por ID
@app.get("/posts", response_model=list[PostPublic])
def read_posts(
    db: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 20,
) -> list[Post]:
    posts = db.exec(select(Post).offset(offset).limit(limit)).all()
    return list(posts)


@app.get("/posts/{post_id}", response_model=PostPublic)
def read_post(post_id: int, db: SessionDep) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    return post


# TODO 5: Actualización parcial (PATCH) y eliminación (DELETE 204)
@app.patch("/posts/{post_id}", response_model=PostPublic)
def update_post(post_id: int, data: PostUpdate, db: SessionDep) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    post.sqlmodel_update(update_data)

    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: SessionDep) -> None:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    db.delete(post)
    db.commit()
# ═══════════════ 🔎 PRUEBA (cuando el CRUD funcione) ═══════════════
# En /docs crea un post enviando TAMBIÉN  "id": 999  y  "created_at": "2000-01-01T00:00:00".
# ¿Qué pasó? Con una sola clase, el cliente decide campos que no debería controlar.
# Con PATCH, además, tendrías que enviar TODOS los campos. Eso nos lleva a la parte 3.



# 🤔 PREGUNTA PARA LA CLASE 2:
# Ahora enviamos author_id en el cuerpo de POST /posts. ¿Qué impide que yo publique
# a nombre de otra persona?

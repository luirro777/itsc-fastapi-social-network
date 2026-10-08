"""CLASE 1 — ESQUELETO: una API que guarda datos (FastAPI + SQLModel + SQLite).

Ejecutar:   uvicorn main:app --reload      →   http://127.0.0.1:8000/docs
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


# ═══════════════ PARTE 2: la tabla Post y su CRUD ═══════════════
class Post(SQLModel, table=True):  # table=True → esta clase ES una tabla
    __tablename__ = "posts"

    id: int | None = Field(default=None, primary_key=True)
    # TODO 2: agrega los campos de la tabla
    #   title: str          (1 a 100 caracteres)   → Field(min_length=1, max_length=100)
    #   content: str        (1 a 2000 caracteres)
    #   created_at: datetime (por defecto, la hora actual)  → Field(default_factory=utcnow)
    # Después de cambiar una tabla: borra clase1.db y reinicia.


# TODO 3: crear un post.  Patrón de SQLModel para guardar:
#         db.add(objeto)  →  db.commit()  →  db.refresh(objeto)  →  return objeto
@app.post("/posts", response_model=Post, status_code=201)
def create_post(post: Post, db: SessionDep):
    raise HTTPException(501, "TODO 3: crear un post")


# TODO 4: leer.
#   · GET /posts           → lista con paginación (offset y limit, máximo 100)
#                            pista: db.exec(select(Post).offset(offset).limit(limit)).all()
#   · GET /posts/{post_id} → un post, o 404 si no existe (pista: db.get(Post, post_id))
@app.get("/posts", response_model=list[Post])
def read_posts(db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20):
    raise HTTPException(501, "TODO 4: listar posts")


@app.get("/posts/{post_id}", response_model=Post)
def read_post(post_id: int, db: SessionDep):
    raise HTTPException(501, "TODO 4: leer un post")


# TODO 5: editar y borrar (ambos con 404 si no existe).
#   · PATCH  → pista: post.sqlmodel_update(datos_enviados) y luego add/commit/refresh
#   · DELETE → pista: db.delete(post) y db.commit()  (responde 204, sin cuerpo)
@app.patch("/posts/{post_id}", response_model=Post)
def update_post(post_id: int, data: Post, db: SessionDep):
    raise HTTPException(501, "TODO 5: editar un post")


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: SessionDep):
    raise HTTPException(501, "TODO 5: borrar un post")


# ═══════════════ 🔎 PRUEBA (cuando el CRUD funcione) ═══════════════
# En /docs crea un post enviando TAMBIÉN  "id": 999  y  "created_at": "2000-01-01T00:00:00".
# ¿Qué pasó? Con una sola clase, el cliente decide campos que no debería controlar.
# Con PATCH, además, tendrías que enviar TODOS los campos. Eso nos lleva a la parte 3.


# ═══════════════ PARTE 3: tablas vs. schemas ═══════════════
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


# 🤔 PREGUNTA PARA LA CLASE 2:
# Ahora enviamos author_id en el cuerpo de POST /posts. ¿Qué impide que yo publique
# a nombre de otra persona?

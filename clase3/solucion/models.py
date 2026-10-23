"""Tablas (table=True) y schemas de la API."""
import enum
from datetime import datetime, timezone
from typing import Annotated

from pydantic import StringConstraints
from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


# ═══════════════ Usuarios ═══════════════
class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=50, unique=True, index=True)


class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: int | None = Field(default=None, primary_key=True)
    hashed_password:str
    role: Role = Field(default=Role.USER)
    posts: list["Post"] = Relationship(back_populates="author")


class UserCreate(UserBase):  # ENTRA al registrarse: tiene password, NO tiene role
    password: Password


class UserPublic(UserBase):  # SALE: vista pública
    id: int


class UserMe(UserPublic):  # SALE: vista privada, solo para el propio usuario
    role: Role


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# ═══════════════ Posts ═══════════════
class PostBase(SQLModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)


class Post(PostBase, table=True):
    __tablename__ = "posts"

    id: int | None = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="users.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utcnow)
    author: User = Relationship(back_populates="posts")


class PostCreate(PostBase):    
    pass


class PostUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1, max_length=2000)


class PostPublic(PostBase):
    id: int
    author_id: int
    created_at: datetime


class PostWithLikes(PostPublic):  # SALE: el post + cuántos likes tiene (se calcula, no se guarda)
    likes_count: int


# ═══════════════ Likes ═══════════════
# TODO 1: crea la tabla de ENLACE  class Like(SQLModel, table=True)  (muchos-a-muchos users ↔ posts)
#   __tablename__ = "likes"
#   user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
#   post_id: int = Field(foreign_key="posts.id", primary_key=True, ondelete="CASCADE")
#   created_at: datetime = Field(default_factory=utcnow)
#
#   Dos campos con primary_key=True = clave primaria COMPUESTA (user_id, post_id).
#   Pregunta: ¿qué impide la base de datos con esta clave? ¿Y con ondelete="CASCADE"?
#   (Borra clase3.db y reinicia después de agregar la tabla.)
class Like(SQLModel, table=True):
   __tablename__ = "likes"
   user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
   post_id: int = Field(foreign_key="posts.id", primary_key=True, ondelete="CASCADE")
   created_at: datetime = Field(default_factory=utcnow)

   
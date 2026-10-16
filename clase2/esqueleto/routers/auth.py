"""Registro, login y 'quién soy'."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from dependencies import CurrentUser, SessionDep, credentials_error
from models import Token, User, UserCreate, UserMe
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserMe, status_code=201)
def register(data: UserCreate, db: SessionDep):
    # TODO 2: registrar un usuario
    #   a) si ya existe un User con ese username → 409 (status.HTTP_409_CONFLICT)
    #      pista: db.exec(select(User).where(User.username == data.username)).first()
    #   b) crear User(username=data.username, hashed_password=hash_password(data.password))
    #      → la contraseña en claro NUNCA se guarda
    #   c) db.add → db.commit → db.refresh → return user
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 2: registro")


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep):
    # TODO 3: iniciar sesión (el formulario trae form.username y form.password)
    #   a) busca el User por username
    #   b) si no existe, o verify_password(form.password, user.hashed_password) es False
    #      → raise credentials_error()      (mismo error para ambos casos: ¿por qué?)
    #   c) return Token(access_token=create_access_token(user.id))
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "TODO 3: login")


@router.get("/me", response_model=UserMe)
def me(current_user: CurrentUser):  # ya resuelto: funciona cuando hagas el TODO 4
    return current_user

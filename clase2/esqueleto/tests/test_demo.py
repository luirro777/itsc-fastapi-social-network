"""TODO 8: ejecuta  pytest -q  ahora (verás rojo) y otra vez al terminar los TODO 1-7 (verde).
Así sabes que terminaste sin probar a mano cada endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database import get_session
from main import app


@pytest.fixture()
def client():
    # Base de datos en memoria: cada test empieza de cero y no toca clase2.db
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)  # sin `with`: no ejecuta el lifespan (que usaría la BD real)
    app.dependency_overrides.clear()


def register_and_login(client, username: str) -> dict:
    body = {"username": username, "password": "supersecreta123"}
    assert client.post("/auth/register", json=body).status_code == 201
    r = client.post("/auth/login", data=body)  # el login usa formulario, no JSON
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_ignores_role_sent_by_client(client):
    r = client.post(
        "/auth/register",
        json={"username": "mallory", "password": "supersecreta123", "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "user"
    assert "hashed_password" not in r.json()


def test_post_author_comes_from_the_token(client):
    alice = register_and_login(client, "alice")
    r = client.post("/posts", json={"title": "Hola", "content": "Primer post"}, headers=alice)
    assert r.status_code == 201
    assert r.json()["author_id"] == client.get("/auth/me", headers=alice).json()["id"]


def test_401_without_token_and_403_for_non_author(client):
    alice, bob = register_and_login(client, "alice"), register_and_login(client, "bob")
    post = {"title": "Mío", "content": "De alice"}

    assert client.post("/posts", json=post).status_code == 401  # sin token: ¿quién eres?
    post_id = client.post("/posts", json=post, headers=alice).json()["id"]

    assert client.patch(f"/posts/{post_id}", json={"title": "hack"}, headers=bob).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=bob).status_code == 403
    assert client.patch(f"/posts/{post_id}", json={"title": "ok"}, headers=alice).status_code == 200
    assert client.delete(f"/posts/{post_id}", headers=alice).status_code == 204
    assert client.get(f"/posts/{post_id}").status_code == 404

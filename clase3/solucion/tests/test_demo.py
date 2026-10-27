"""TODO 7: ejecuta  pytest -q  ahora (verás rojo) y otra vez al terminar los TODO 1-6 (verde).
TODO 8: al final de este archivo hay un test para que lo escribas tú."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from database import get_session
from main import app


@pytest.fixture()
def engine():
    # Base de datos en memoria: cada test empieza de cero y no toca clase3.db
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def client(engine):
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


def new_post(client, headers, title="Hola") -> int:
    r = client.post("/posts", json={"title": title, "content": "contenido"}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


# ── Regresión: lo de la clase 2 sigue funcionando ──────────────────────────────
def test_401_without_token_and_403_for_non_author(client):
    alice, bob = register_and_login(client, "alice"), register_and_login(client, "bob")
    post_id = new_post(client, alice)

    assert client.post("/posts", json={"title": "x", "content": "y"}).status_code == 401
    assert client.patch(f"/posts/{post_id}", json={"title": "hack"}, headers=bob).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=bob).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=alice).status_code == 204


# ── Likes ──────────────────────────────────────────────────────────────────────
def test_post_without_likes_shows_zero(client):
    # Si usaste un JOIN común en vez de LEFT JOIN, este post "desaparece" y el test falla.
    alice = register_and_login(client, "alice")
    post_id = new_post(client, alice)

    assert client.get(f"/posts/{post_id}").json()["likes_count"] == 0
    assert [p["likes_count"] for p in client.get("/posts").json()] == [0]


def test_like_increments_count_in_list_and_detail(client):
    alice, bob = register_and_login(client, "alice"), register_and_login(client, "bob")
    liked, ignored = new_post(client, alice, "gustado"), new_post(client, alice, "ignorado")

    r = client.put(f"/posts/{liked}/like", headers=bob)
    assert r.status_code == 200
    assert r.json()["likes_count"] == 1

    counts = {p["id"]: p["likes_count"] for p in client.get("/posts").json()}
    assert counts == {liked: 1, ignored: 0}
    assert client.get(f"/posts/{liked}").json()["likes_count"] == 1


def test_like_is_idempotent(client):
    alice, bob = register_and_login(client, "alice"), register_and_login(client, "bob")
    post_id = new_post(client, alice)

    assert client.put(f"/posts/{post_id}/like", headers=bob).status_code == 200
    r = client.put(f"/posts/{post_id}/like", headers=bob)  # segunda vez: no rompe ni duplica
    assert r.status_code == 200
    assert r.json()["likes_count"] == 1


def test_many_users_like_the_same_post(client):
    alice = register_and_login(client, "alice")
    post_id = new_post(client, alice)
    for name in ("bob", "carol", "dave"):
        client.put(f"/posts/{post_id}/like", headers=register_and_login(client, name))

    assert client.get(f"/posts/{post_id}").json()["likes_count"] == 3
    likers = client.get(f"/posts/{post_id}/likes").json()
    assert sorted(u["username"] for u in likers) == ["bob", "carol", "dave"]
    assert all("hashed_password" not in u for u in likers)


def test_unlike_and_unlike_again(client):
    alice, bob = register_and_login(client, "alice"), register_and_login(client, "bob")
    post_id = new_post(client, alice)
    client.put(f"/posts/{post_id}/like", headers=bob)

    r = client.delete(f"/posts/{post_id}/like", headers=bob)
    assert r.status_code == 200
    assert r.json()["likes_count"] == 0
    assert client.delete(f"/posts/{post_id}/like", headers=bob).status_code == 200  # idempotente


def test_like_errors_401_and_404(client):
    alice = register_and_login(client, "alice")
    post_id = new_post(client, alice)

    assert client.put(f"/posts/{post_id}/like").status_code == 401  # sin token
    assert client.put("/posts/9999/like", headers=alice).status_code == 404
    assert client.delete("/posts/9999/like", headers=alice).status_code == 404
    assert client.get("/posts/9999/likes").status_code == 404


def test_user_likes_endpoint(client):
    alice, bob = register_and_login(client, "alice"), register_and_login(client, "bob")
    p1, p2, _ = (new_post(client, alice, t) for t in ("uno", "dos", "tres"))
    client.put(f"/posts/{p1}/like", headers=bob)
    client.put(f"/posts/{p2}/like", headers=bob)
    client.put(f"/posts/{p1}/like", headers=alice)  # el like de alice no cuenta para bob

    bob_id = client.get("/auth/me", headers=bob).json()["id"]
    liked = client.get(f"/users/{bob_id}/likes").json()
    assert sorted(p["id"] for p in liked) == sorted([p1, p2])
    assert client.get("/users/9999/likes").status_code == 404


def test_deleting_a_post_deletes_its_likes(client, engine):
    # TODO 8: A este lo escriben uds, mis polluelos del ITSC. Plan:
    #   1) alice crea un post, bob le da like (PUT /posts/{id}/like)
    #   2) comprueba en la BD que hay 1 fila en la tabla Like:
    #        with Session(engine) as db:
    #            assert len(db.exec(select(Like)).all()) == 1
    #      (importa Like desde models)
    #   3) alice borra el post (DELETE /posts/{id}) → 204
    #   4) vuelve a mirar la tabla Like: tiene que estar vacía (ON DELETE CASCADE)
    #   Bonus: comenta ondelete="CASCADE" en models.py, borra clase3.db y mira cómo falla el test.
    #pytest.fail("TODO 8: escribe este test")
    from models import Like
    alice = register_and_login(client, "alice")
    bob = register_and_login(client, "bob")
    post_id = new_post(client, alice)
    client.put(f"/posts/{post_id}/like", headers = bob).status_code == 200
    with Session(engine) as db:
        assert len(db.exec(select(Like)).all()) == 1
    assert client.delete(f"/posts/{post_id}", headers = alice).status_code == 204
    with Session(engine) as db:
            assert db.exec(select(Like)).all() == []


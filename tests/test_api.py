import pytest

pytest.importorskip("fastapi")  # estes testes precisam do FastAPI instalado

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RANKING_DB", str(tmp_path / "teste.db"))
    monkeypatch.delenv("API_KEY", raising=False)
    return TestClient(app)


def create(client, nome):
    response = client.post("/jogadores", json={"nome": nome})
    assert response.status_code == 201, response.text
    return response.json()


def test_root(client):
    assert client.get("/").json()["status"] == "ok"


def test_create_player(client):
    player = create(client, "Guilherme")
    assert player["nome"] == "Guilherme"
    assert player["pontos"] == 0
    assert player["partidas"] == 0


def test_duplicate_name_returns_409(client):
    create(client, "Guilherme")
    response = client.post("/jogadores", json={"nome": "GUILHERME"})
    assert response.status_code == 409


@pytest.mark.parametrize("nome", ["ab", "nome com espaço", "x" * 21, ""])
def test_invalid_name_returns_422(client, nome):
    assert client.post("/jogadores", json={"nome": nome}).status_code == 422


def test_player_not_found(client):
    assert client.get("/jogadores/999").status_code == 404
    assert client.post("/jogadores/999/partidas", json={"pontos": 10}).status_code == 404
    assert client.get("/jogadores/999/partidas").status_code == 404
    assert client.delete("/jogadores/999").status_code == 404


def test_matches_and_ranking(client):
    ana = create(client, "Ana")
    bia = create(client, "Bia")

    client.post(f"/jogadores/{ana['id']}/partidas", json={"pontos": 100})
    response = client.post(f"/jogadores/{bia['id']}/partidas", json={"pontos": 250})
    assert response.status_code == 201
    assert response.json()["pontos"] == 250

    ranking = client.get("/ranking").json()
    assert [(r["posicao"], r["nome"], r["pontos"]) for r in ranking] == [
        (1, "Bia", 250),
        (2, "Ana", 100),
    ]
    assert len(client.get("/ranking?limite=1").json()) == 1

    matches = client.get(f"/jogadores/{ana['id']}/partidas").json()
    assert [m["pontos"] for m in matches] == [100]


def test_negative_points_rejected(client):
    player = create(client, "Ana")
    response = client.post(f"/jogadores/{player['id']}/partidas", json={"pontos": -5})
    assert response.status_code == 422


def test_delete_player(client):
    player = create(client, "Ana")
    assert client.delete(f"/jogadores/{player['id']}").status_code == 204
    assert client.get(f"/jogadores/{player['id']}").status_code == 404


def test_api_key_protects_writes(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "segredo123")

    assert client.post("/jogadores", json={"nome": "Ana"}).status_code == 401
    assert (
        client.post("/jogadores", json={"nome": "Ana"}, headers={"X-API-Key": "errada"}).status_code
        == 401
    )
    ok = client.post("/jogadores", json={"nome": "Ana"}, headers={"X-API-Key": "segredo123"})
    assert ok.status_code == 201

    # leitura continua liberada
    assert client.get("/ranking").status_code == 200

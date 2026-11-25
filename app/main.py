"""Rotas da API de ranking de jogadores.

Rodar localmente:
    uvicorn app.main:app --reload
Documentação interativa:
    http://127.0.0.1:8000/docs
"""

import os
import secrets
from collections.abc import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status

from .database import DuplicateNameError, Repository, connect
from .schemas import (
    Match,
    MatchCreate,
    Player,
    PlayerCreate,
    RankingEntry,
    to_match,
    to_player,
    to_ranking_entry,
)

app = FastAPI(
    title="Ranking de Jogadores API",
    description="Cadastre jogadores, registre partidas e consulte o placar dos melhores.",
    version="1.0.0",
)


# ---------- dependências ----------

def get_repo() -> Iterator[Repository]:
    """Abre uma conexão por requisição e fecha no final."""
    conn = connect(os.environ.get("RANKING_DB", "ranking.db"))
    try:
        yield Repository(conn)
    finally:
        conn.close()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Se a variável API_KEY estiver definida, as rotas que alteram dados exigem a chave."""
    expected = os.environ.get("API_KEY")
    if expected and not (x_api_key and secrets.compare_digest(x_api_key, expected)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chave de API inválida ou ausente")


def get_player_or_404(player_id: int, repo: Repository) -> dict:
    player = repo.get_player(player_id)
    if player is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jogador não encontrado")
    return player


# ---------- rotas ----------

@app.get("/", tags=["status"])
def root() -> dict:
    return {"status": "ok", "docs": "/docs"}


@app.post(
    "/jogadores",
    response_model=Player,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    tags=["jogadores"],
)
def create_player(data: PlayerCreate, repo: Repository = Depends(get_repo)) -> Player:
    try:
        return to_player(repo.create_player(data.nome))
    except DuplicateNameError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"O nome {data.nome!r} já está em uso")


@app.get("/jogadores", response_model=list[Player], tags=["jogadores"])
def list_players(repo: Repository = Depends(get_repo)) -> list[Player]:
    return [to_player(p) for p in repo.list_players()]


@app.get("/jogadores/{player_id}", response_model=Player, tags=["jogadores"])
def get_player(player_id: int, repo: Repository = Depends(get_repo)) -> Player:
    return to_player(get_player_or_404(player_id, repo))


@app.delete(
    "/jogadores/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    tags=["jogadores"],
)
def delete_player(player_id: int, repo: Repository = Depends(get_repo)) -> None:
    if not repo.delete_player(player_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jogador não encontrado")


@app.post(
    "/jogadores/{player_id}/partidas",
    response_model=Player,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    tags=["partidas"],
)
def add_match(player_id: int, data: MatchCreate, repo: Repository = Depends(get_repo)) -> Player:
    player = repo.add_match(player_id, data.pontos)
    if player is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jogador não encontrado")
    return to_player(player)


@app.get("/jogadores/{player_id}/partidas", response_model=list[Match], tags=["partidas"])
def list_matches(player_id: int, repo: Repository = Depends(get_repo)) -> list[Match]:
    get_player_or_404(player_id, repo)
    return [to_match(m) for m in repo.list_matches(player_id)]


@app.get("/ranking", response_model=list[RankingEntry], tags=["ranking"])
def ranking(
    limite: int = Query(default=10, ge=1, le=100, description="Quantos jogadores mostrar"),
    repo: Repository = Depends(get_repo),
) -> list[RankingEntry]:
    return [to_ranking_entry(r) for r in repo.ranking(limite)]

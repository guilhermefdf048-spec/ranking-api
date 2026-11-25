"""Formatos de entrada e saída da API (validados pelo Pydantic)."""

from datetime import datetime

from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    nome: str = Field(
        min_length=3,
        max_length=20,
        pattern=r"^[A-Za-z0-9_]+$",
        description="Letras, números e _ (3 a 20 caracteres)",
        examples=["Guilherme_07"],
    )


class MatchCreate(BaseModel):
    pontos: int = Field(ge=0, le=1_000_000, description="Pontos feitos na partida", examples=[150])


class Player(BaseModel):
    id: int
    nome: str
    pontos: int
    partidas: int
    criado_em: datetime


class Match(BaseModel):
    id: int
    pontos: int
    jogada_em: datetime


class RankingEntry(BaseModel):
    posicao: int
    id: int
    nome: str
    pontos: int
    partidas: int


def to_player(row: dict) -> Player:
    """Converte a linha do banco (nomes em inglês) para o formato da API."""
    return Player(
        id=row["id"],
        nome=row["name"],
        pontos=row["points"],
        partidas=row["matches"],
        criado_em=row["created_at"],
    )


def to_match(row: dict) -> Match:
    return Match(id=row["id"], pontos=row["points"], jogada_em=row["played_at"])


def to_ranking_entry(row: dict) -> RankingEntry:
    return RankingEntry(
        posicao=row["position"],
        id=row["id"],
        nome=row["name"],
        pontos=row["points"],
        partidas=row["matches"],
    )

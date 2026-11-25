"""Acesso ao banco de dados SQLite: jogadores, partidas e ranking."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    points      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id   INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    points      INTEGER NOT NULL,
    played_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_players_points ON players(points DESC);
"""

# Seleciona o jogador já com o número de partidas jogadas
PLAYER_QUERY = """
SELECT p.id, p.name, p.points, p.created_at, COUNT(m.id) AS matches
FROM players p
LEFT JOIN matches m ON m.player_id = p.id
"""


class DuplicateNameError(Exception):
    """Já existe um jogador com esse nome."""


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Repository:
    """Todas as operações no banco ficam aqui, separadas das rotas da API."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ---------- jogadores ----------

    def create_player(self, name: str) -> dict:
        try:
            with self.conn:  # abre uma transação e faz commit no final
                cursor = self.conn.execute(
                    "INSERT INTO players (name, created_at) VALUES (?, ?)",
                    (name, _now()),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateNameError(name) from exc
        return self.get_player(cursor.lastrowid)

    def get_player(self, player_id: int) -> dict | None:
        row = self.conn.execute(
            PLAYER_QUERY + " WHERE p.id = ? GROUP BY p.id", (player_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_players(self) -> list[dict]:
        rows = self.conn.execute(PLAYER_QUERY + " GROUP BY p.id ORDER BY p.name").fetchall()
        return [dict(r) for r in rows]

    def delete_player(self, player_id: int) -> bool:
        with self.conn:
            cursor = self.conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
        return cursor.rowcount > 0

    # ---------- partidas ----------

    def add_match(self, player_id: int, points: int) -> dict | None:
        """Registra uma partida e soma os pontos ao total do jogador."""
        if self.get_player(player_id) is None:
            return None
        with self.conn:
            self.conn.execute(
                "INSERT INTO matches (player_id, points, played_at) VALUES (?, ?, ?)",
                (player_id, points, _now()),
            )
            self.conn.execute(
                "UPDATE players SET points = points + ? WHERE id = ?",
                (points, player_id),
            )
        return self.get_player(player_id)

    def list_matches(self, player_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, points, played_at FROM matches WHERE player_id = ? ORDER BY id DESC",
            (player_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------- ranking ----------

    def ranking(self, limit: int = 10) -> list[dict]:
        """Melhores jogadores. Em caso de empate, quem chegou primeiro fica na frente."""
        rows = self.conn.execute(
            PLAYER_QUERY + " GROUP BY p.id ORDER BY p.points DESC, p.id ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"position": i, **dict(r)} for i, r in enumerate(rows, start=1)]

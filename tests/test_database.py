import pytest

from app.database import DuplicateNameError, Repository, connect


@pytest.fixture
def repo():
    conn = connect(":memory:")
    yield Repository(conn)
    conn.close()


def test_create_and_get_player(repo):
    player = repo.create_player("Guilherme")
    assert player["name"] == "Guilherme"
    assert player["points"] == 0
    assert player["matches"] == 0
    assert repo.get_player(player["id"]) == player


def test_duplicate_name_ignores_case(repo):
    repo.create_player("Guilherme")
    with pytest.raises(DuplicateNameError):
        repo.create_player("guilherme")


def test_get_missing_player(repo):
    assert repo.get_player(999) is None


def test_add_match_sums_points(repo):
    pid = repo.create_player("Ana")["id"]
    repo.add_match(pid, 100)
    player = repo.add_match(pid, 50)
    assert player["points"] == 150
    assert player["matches"] == 2
    assert [m["points"] for m in repo.list_matches(pid)] == [50, 100]  # mais recente primeiro


def test_add_match_missing_player(repo):
    assert repo.add_match(999, 10) is None


def test_ranking_order_and_tiebreak(repo):
    a = repo.create_player("Ana")["id"]
    b = repo.create_player("Bia")["id"]
    c = repo.create_player("Caio")["id"]
    repo.add_match(a, 100)
    repo.add_match(b, 300)
    repo.add_match(c, 100)  # empata com Ana, mas foi criado depois

    ranking = repo.ranking()
    assert [(r["position"], r["name"]) for r in ranking] == [(1, "Bia"), (2, "Ana"), (3, "Caio")]
    assert len(repo.ranking(limit=2)) == 2


def test_delete_player_removes_matches(repo):
    pid = repo.create_player("Ana")["id"]
    repo.add_match(pid, 10)
    assert repo.delete_player(pid) is True
    assert repo.get_player(pid) is None
    assert repo.list_matches(pid) == []
    assert repo.delete_player(pid) is False


def test_list_players_sorted_by_name(repo):
    for name in ["Caio", "Ana", "Bia"]:
        repo.create_player(name)
    assert [p["name"] for p in repo.list_players()] == ["Ana", "Bia", "Caio"]

import sqlite3

import pytest

from src.data_generation import AS_OF, HISTORY_DAYS, generate
from src.database import create_database, load


def test_seed_reproducibility():
    assert generate(42) == generate(42)
    assert generate(42) != generate(43)


def test_sqlite_references_and_dates(tmp_path):
    path = create_database(tmp_path / "data.sqlite")
    with sqlite3.connect(path) as conn:
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        assert conn.execute("SELECT COUNT(DISTINCT day) FROM fx").fetchone()[0] == HISTORY_DAYS
    rows = load(path)
    assert rows == load()
    assert all(p["outcome_day"] is None or p["instructed"] <= p["outcome_day"] <= str(AS_OF)
               for p in rows["payments"])


def test_database_refuses_overwrite(tmp_path):
    path = create_database(tmp_path / "data.sqlite")
    with pytest.raises(FileExistsError):
        create_database(path)
    assert load(path) == load()

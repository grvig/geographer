import sqlite3

import pytest

from geographer_pipeline.cache import MIGRATIONS, SCHEMA_VERSION, CacheError, connect


def test_creates_schema_once_and_reopens(tmp_path):
    path = tmp_path / "nested" / "cache.sqlite"
    db = connect(path)
    tables = {row["name"] for row in db.execute("SELECT name FROM sqlite_master")}
    assert {"images", "detections", "embeddings", "matches"} <= tables
    db.close()
    # Reopening must not try to create the tables again.
    connect(path).close()


def test_upgrades_an_older_cache_in_place(tmp_path):
    path = tmp_path / "cache.sqlite"
    old = sqlite3.connect(path)
    old.executescript(MIGRATIONS[0])
    old.execute(
        "INSERT INTO images (id, area, sequence, lon, lat, is_pano,"
        " captured_at, creator, width, height, thumb_url)"
        " VALUES ('1', 'a', 's', 0, 0, 0, 0, '', 1, 1, '')"
    )
    old.execute("PRAGMA user_version = 1")
    old.commit()
    old.close()
    db = connect(path)
    assert db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert db.execute("SELECT id FROM images").fetchone()["id"] == "1"
    assert db.execute("SELECT count(*) FROM matches").fetchone()[0] == 0


def test_rejects_a_cache_from_a_newer_schema_version(tmp_path):
    path = tmp_path / "cache.sqlite"
    old = sqlite3.connect(path)
    old.execute("PRAGMA user_version = 99")
    old.close()
    with pytest.raises(CacheError, match="newer"):
        connect(path)

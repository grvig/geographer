import sqlite3

import pytest

from geographer_pipeline.cache import CacheError, connect


def test_creates_schema_once_and_reopens(tmp_path):
    path = tmp_path / "nested" / "cache.sqlite"
    db = connect(path)
    tables = {row["name"] for row in db.execute("SELECT name FROM sqlite_master")}
    assert {"images", "detections"} <= tables
    db.close()
    # Reopening must not try to create the tables again.
    connect(path).close()


def test_rejects_a_cache_from_another_schema_version(tmp_path):
    path = tmp_path / "cache.sqlite"
    old = sqlite3.connect(path)
    old.execute("PRAGMA user_version = 99")
    old.close()
    with pytest.raises(CacheError, match="Delete the file"):
        connect(path)

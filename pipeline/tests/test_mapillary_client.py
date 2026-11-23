from types import SimpleNamespace

import pytest
import requests

from geographer_pipeline.mapillary.client import (
    MapillaryClient,
    MapillaryError,
    load_token,
)


def response(status, content=b""):
    return SimpleNamespace(status_code=status, ok=status < 400, content=content)


def make_client(*outcomes):
    queue = list(outcomes)
    calls = []

    def get(url, params=None, timeout=None):
        calls.append(url)
        outcome = queue.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    session = SimpleNamespace(headers={}, get=get)
    waits = []
    client = MapillaryClient("MLY|1|secret", session=session, sleep=waits.append)
    return client, calls, waits


def test_retries_rate_limit_and_network_errors_with_backoff():
    client, _, waits = make_client(
        response(429), requests.ConnectionError(), response(200, b"tile")
    )
    assert client.tile(14, 1, 2) == b"tile"
    assert waits == [1.0, 2.0]
    assert client.session.headers["Authorization"] == "OAuth MLY|1|secret"


def test_gives_up_after_retries_without_leaking_token():
    client, _, waits = make_client(*[response(503) for _ in range(5)])
    with pytest.raises(MapillaryError, match="503") as error:
        client.tile(14, 1, 2)
    assert "secret" not in str(error.value)
    assert len(waits) == 4


def test_client_errors_are_not_retried():
    client, calls, _ = make_client(response(401))
    with pytest.raises(MapillaryError):
        client.get("https://graph.mapillary.com/123")
    assert len(calls) == 1


def test_token_comes_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("MAPILLARY_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    with pytest.raises(MapillaryError, match="MAPILLARY_TOKEN"):
        load_token(env_file)
    env_file.write_text("MAPILLARY_TOKEN= MLY|9|abc \n")
    assert load_token(env_file) == "MLY|9|abc"

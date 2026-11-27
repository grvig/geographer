from fastapi.testclient import TestClient

from geographer_pipeline.curate.server import Paths, create_app


def client(paths=None):
    return TestClient(create_app(paths or Paths()))


def test_health_and_areas():
    api = client()
    assert api.get("/api/health").json() == {"ok": True}
    areas = api.get("/api/areas").json()
    assert {"name": "saulieu", "country": "FR"} in areas


def test_no_interactive_docs_are_served():
    assert client().get("/docs").status_code == 404

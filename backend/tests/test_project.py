import pytest
from fastapi.testclient import TestClient

from api.routes import project as project_module
from api.routes.brief import EXAMPLE_BRIEF
from main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(project_module, "PROJECTS_DIR", tmp_path)
    return TestClient(app)


def test_save_load_roundtrip(client):
    resp = client.post("/api/project/save",
                       json={"name": "atrium-test", "data": EXAMPLE_BRIEF})
    assert resp.status_code == 200
    assert resp.json() == {"saved": True, "name": "atrium-test"}

    resp = client.get("/api/project/atrium-test")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "atrium-test"
    assert body["data"] == EXAMPLE_BRIEF


def test_list_projects(client):
    client.post("/api/project/save", json={"name": "b-project", "data": {}})
    client.post("/api/project/save", json={"name": "a-project", "data": {}})
    assert client.get("/api/project/list").json() == {"projects": ["a-project", "b-project"]}


def test_load_missing_project_404(client):
    assert client.get("/api/project/nope").status_code == 404


def test_invalid_name_rejected(client):
    resp = client.post("/api/project/save", json={"name": "../evil", "data": {}})
    assert resp.status_code == 400

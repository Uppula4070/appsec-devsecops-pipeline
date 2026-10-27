import pytest

from app import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DATABASE", str(tmp_path / "test.db"))
    app_module.init_db()
    return app_module.app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_search_finds_note(client):
    titles = [n["title"] for n in client.get("/notes?q=welc").get_json()]
    assert titles == ["welcome"]


def test_sql_injection_returns_nothing(client):
    # A classic injection payload must be treated as plain text.
    assert client.get("/notes?q=' OR '1'='1").get_json() == []


def test_security_headers(client):
    headers = client.get("/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert "form-action 'none'" in headers["Content-Security-Policy"]
    assert headers["Server"] == "notes-api"

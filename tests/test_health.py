from fastapi.testclient import TestClient

from api.app.main import app


def test_app_imports():
    client = TestClient(app)
    assert client is not None

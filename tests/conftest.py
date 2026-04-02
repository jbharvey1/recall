import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test.db")

@pytest.fixture
def app(tmp_db, monkeypatch):
    monkeypatch.setenv("DB_PATH", tmp_db)
    import importlib
    import config
    importlib.reload(config)
    from app import create_app
    app = create_app(tmp_db)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

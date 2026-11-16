import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app  # noqa: E402

ADMIN = ("admin@cupcakestore.com", "Admin@123")
CLIENT = ("cliente@email.com", "Cliente@123")


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite"),
                      "WTF_CSRF_ENABLED": False, "UPLOAD_FOLDER": str(tmp_path)})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, creds):
    return client.post("/login", data={"email": creds[0], "password": creds[1]}, follow_redirects=True)


@pytest.fixture
def client_logged(client):
    login(client, CLIENT)
    return client


@pytest.fixture
def admin_logged(client):
    login(client, ADMIN)
    return client

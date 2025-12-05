import pytest
from config import Config
from app import create_app, db
from app.models import User

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

# ---------------------------------------------------------------------
def test_register_ok(client):
    resp = client.post("/auth/register", data={
        "username": "user1",
        "email": "user1@email.com",
        "password": "H@sl0",
        "password2": "H@sl0"
    }, follow_redirects=True)

    assert b"registered" in resp.data.lower()


def test_register_wrong_username(client, app): # userbname istnieje
    with app.app_context():
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add(u2)
        db.session.commit()

    resp = client.post("/auth/register", data={
        "username": "user2",
        "email": "user2@innyemail.com",
        "password": "H@sl0",
        "password2": "H@sl0"
    }, follow_redirects=True)

    assert b"different username" in resp.data.lower()

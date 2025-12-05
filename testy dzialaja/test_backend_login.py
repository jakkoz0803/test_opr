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
def test_login_ok(client, app):
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        db.session.add(u1)
        db.session.commit()

    resp = client.post("/auth/login", data={
        "username": "user1",
        "password": "H@sl0"
    }, follow_redirects=True)

    assert b"logout" in resp.data.lower()


def test_login_wrong_password(client, app):
    with app.app_context():
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add(u2)
        db.session.commit()

    resp = client.post("/auth/login", data={
        "username": "user2",
        "password": "zlehaslo"
    }, follow_redirects=True)

    assert b"invalid username or password" in resp.data.lower()

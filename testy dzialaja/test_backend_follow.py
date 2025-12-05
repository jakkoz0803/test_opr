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

def login(client, username, password):
    client.post("/auth/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

# ---------------------------------------------------------------------
def test_follow_ok(client, app):
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add_all([u1, u2])
        db.session.commit()

    login(client, "user1", "H@sl0")

    resp = client.post("/follow/user2", follow_redirects=True)

    assert b"you are following" in resp.data.lower()


def test_follow_self(client, app): # nie powinno sie dac followowac samego siebie
    with app.app_context():
        u3 = User(username="user3", email="user3@email.com")
        u3.set_password("H@sl0")
        db.session.add(u3)
        db.session.commit()

    login(client, "user3", "H@sl0")

    resp = client.post("/follow/user3", follow_redirects=True)

    assert b"cannot follow yourself" in resp.data.lower()

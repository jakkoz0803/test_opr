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
def test_post_ok(client, app): # tworzenie postu
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        db.session.add(u1)
        db.session.commit()

    login(client, "user1", "H@sl0")

    resp = client.post("/index", data={"post": "post dziala"}, follow_redirects=True)

    assert b"your post is now live" in resp.data.lower()


def test_post_empty(client, app):
    with app.app_context():
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add(u2)
        db.session.commit()

    login(client, "user2", "H@sl0")

    resp = client.post("/index", data={"post": ""}, follow_redirects=True)

    assert b"this field is required" in resp.data.lower()

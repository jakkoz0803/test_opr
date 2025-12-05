import pytest
from config import Config
from app import create_app, db
from app.models import User, Message

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
def test_message_ok(client, app): # u1 - wysyla wiadomosc, u2 - dostaje wiadomosc
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add_all([u1, u2])
        db.session.commit()
        u1_id = u1.id
        u2_id = u2.id

    login(client, "user1", "H@sl0")

    resp = client.post("/send_message/user2", data={"message": "wiadomosc do user2"}, follow_redirects=True)

    assert b"your message has been sent" in resp.data.lower()

    with app.app_context():
        msgs = Message.query.filter_by(sender_id=u1_id, recipient_id=u2_id).all()

        assert len(msgs) == 1 # sprawdza, czy w bazie powstala jedna wiadomosc
        assert msgs[0].body == "wiadomosc do user2" # sprawdza, czy tresc wiadomosci sie zgadza

def test_message_empty(client, app):  # pusta wiadomosc
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add_all([u1, u2])
        db.session.commit()

    login(client, "user1", "H@sl0")

    resp = client.post("/send_message/user2", data={"message": ""}, follow_redirects=True)

    assert b"message" in resp.data.lower()
    assert b"required" in resp.data.lower()
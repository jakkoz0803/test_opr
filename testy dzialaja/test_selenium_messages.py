import threading
import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By

from app import create_app, db
from app.models import User

class SeleniumConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test"
    POSTS_PER_PAGE = 10
    LANGUAGES = ['en', 'pl']
    ELASTICSEARCH_URL = None
    REDIS_URL = "redis://localhost:6379/0"

@pytest.fixture(scope="session")
def app():
    app = create_app(SeleniumConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield

@pytest.fixture(scope="session")
def live_server(app):
    server = threading.Thread(
        target=app.run,
        kwargs={"port": 5003, "debug": False, "use_reloader": False},
        daemon=True
    )
    server.start()
    time.sleep(1)
    return "http://127.0.0.1:5003"

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

# ---------------------------------------------------------------------
def test_send_message_ok(app, live_server, driver):
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")
        db.session.add_all([u1, u2])
        db.session.commit()

    driver.get(live_server + "/auth/login")
    driver.find_element(By.ID, "username").send_keys("user1")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    driver.get(live_server + "/send_message/user2")
    driver.find_element(By.ID, "message").send_keys("wysylanie wiadomosci dziala")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "your message has been sent" in driver.page_source.lower()

def test_send_message_wrong_user(app, live_server, driver): # uzytkownik nie istnieje
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        db.session.add(u1)
        db.session.commit()

    driver.get(live_server + "/auth/login")
    driver.find_element(By.ID, "username").send_keys("user1")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    driver.get(live_server + "/send_message/user3") # user3 nie istnieje
    time.sleep(1)

    assert "not found" in driver.page_source.lower() or "404" in driver.page_source


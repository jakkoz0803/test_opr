import pytest
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from werkzeug.serving import make_server

from app import create_app, db
from app.models import User

class SeleniumConfig:
    TESTING = True
    SECRET_KEY = "selenium-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = "redis://localhost:6379/0"
    ELASTICSEARCH_URL = None
    POSTS_PER_PAGE = 10

    LANGUAGES = ['en', 'pl']
    ADMINS = ['test@example.com']
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 8025
    MAIL_DEFAULT_SENDER = 'noreply@example.com'


@pytest.fixture
def app():
    app = create_app(SeleniumConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def server(app):
    server = make_server("127.0.0.1", 5004, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    time.sleep(1)
    yield "http://127.0.0.1:5004"
    server.shutdown()

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

# ---------------------------------------------------------------------
def test_follow_ok(app, server, driver):
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")

        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")

        db.session.add_all([u1, u2])
        db.session.commit()

    # logowanie jako user1
    driver.get(server + "/auth/login")
    driver.find_element(By.ID, "username").send_keys("user1")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    # przejscie do profilu user2
    driver.get(server + "/user/user2")
    time.sleep(1)

    # klikamy follow
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Follow"]').click()
    time.sleep(1)

    # sprawdzamy czy pojawia sie unfollow
    assert "Unfollow" in driver.page_source


def test_unfollow_ok(app, server, driver):
    with app.app_context():
        u1 = User(username="user1", email="user1@email.com")
        u1.set_password("H@sl0")
        u2 = User(username="user2", email="user2@email.com")
        u2.set_password("H@sl0")

        db.session.add_all([u1, u2])
        db.session.commit()

        u1.follow(u2)
        db.session.commit()

    # logowanie jako u1
    driver.get(server + "/auth/login")
    driver.find_element(By.ID, "username").send_keys("user1")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    # wejscie na profil u2
    driver.get(server + "/user/user2")
    time.sleep(1)

    # klikamy unfollow
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Unfollow"]').click()
    time.sleep(1)

    # po unfollow powinien pojawic sie follow
    follow_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Follow"]')

    assert follow_button is not None


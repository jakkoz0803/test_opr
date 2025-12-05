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
def test_post_ok(app, server, driver):
    with app.app_context():
        u = User(username="user1", email="user1@email.com")
        u.set_password("H@sl0")
        db.session.add(u)
        db.session.commit()

    driver.get(server + "/auth/login")
    driver.find_element(By.ID, "username").send_keys("user1")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    driver.find_element(By.ID, "post").send_keys("post dziala")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    assert "post dziala" in driver.page_source.lower()


def test_post_empty(app, server, driver):
    with app.app_context():
        u = User(username="user1", email="user1@email.com")
        u.set_password("H@sl0")
        db.session.add(u)
        db.session.commit()

    driver.get(server + "/auth/login")
    driver.find_element(By.ID, "username").send_keys("user1")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    post_input = driver.find_element(By.ID, "post")

    # klikamy submit przy pustym polu
    driver.find_element(By.ID, "submit").click()
    time.sleep(1)

    validation = post_input.get_attribute("validationMessage")

    assert validation != "", "post nie moze byc pusty"

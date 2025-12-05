import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from app import create_app, db
from app.models import User
from config import Config

class SeleniumConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False

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
def live_server(app):
    import threading
    from werkzeug.serving import make_server

    server = make_server("127.0.0.1", 5001, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    time.sleep(1)
    yield
    server.shutdown()

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

@pytest.fixture
def test_user(app):
    with app.app_context():
        u = User(username="user", email="user@email.com")
        u.set_password("H@sl0")
        db.session.add(u)
        db.session.commit()

# ---------------------------------------------------------------------
def test_login_ok(live_server, driver, test_user):
    driver.get("http://127.0.0.1:5001/auth/login")

    driver.find_element(By.ID, "username").send_keys("user")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()

    time.sleep(1)

    assert "logout" in driver.page_source.lower()


def test_login_wrong_password(live_server, driver, test_user):
    driver.get("http://127.0.0.1:5001/auth/login")

    driver.find_element(By.ID, "username").send_keys("user")
    driver.find_element(By.ID, "password").send_keys("zlehaslo")
    driver.find_element(By.ID, "submit").click()

    time.sleep(1)

    assert "invalid username or password" in driver.page_source.lower()

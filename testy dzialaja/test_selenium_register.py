import threading
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from werkzeug.serving import make_server

from app import create_app, db
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

@pytest.fixture(scope="function")
def live_server(app):
    server = make_server("127.0.0.1", 5001, app)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=2)

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

# ---------------------------------------------------------------------
def test_register_ok(live_server, driver):

    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 5)

    driver.get("http://127.0.0.1:5001/auth/register")

    driver.find_element(By.ID, "username").send_keys("user")
    driver.find_element(By.ID, "email").send_keys("user@email.com")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "password2").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()

    alert = driver.find_element(By.CSS_SELECTOR, '[role="alert"]')
    wait.until(lambda _: alert.is_displayed())

    # po poprawnej rejestracji powinna byc strona logowania
    assert "/auth/login" in driver.current_url.lower()


def test_register_duplicate_username(live_server, driver, app):
    with app.app_context():
        from app.models import User
        u = User(username="user2", email="user2@email.com")
        u.set_password("H@sl0")
        db.session.add(u)
        db.session.commit()

    driver.implicitly_wait(10)
    driver.get("http://127.0.0.1:5001/auth/register")

    driver.find_element(By.ID, "username").send_keys("user2")
    driver.find_element(By.ID, "email").send_keys("user2@innyemail.com")
    driver.find_element(By.ID, "password").send_keys("H@sl0")
    driver.find_element(By.ID, "password2").send_keys("H@sl0")
    driver.find_element(By.ID, "submit").click()

    time.sleep(1)

    # pobieramy element z bledem formularza wtforms
    error_box = driver.find_element(By.CSS_SELECTOR, ".invalid-feedback")

    assert error_box.is_displayed()
    assert "different username" in error_box.text.lower()

import pytest, warnings
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"
    with app.test_client() as client:
        yield client


def login(client, remember=False):
    return client.post("/login", data={
        "username": "user",
        "password": "qwerty",
        "remember": "on" if remember else ""
    }, follow_redirects=True)


def test_counter_separate_sessions(client):
    r1 = client.get("/counter")
    r2 = client.get("/counter")
    assert b"2" in r2.data


def test_login_success(client):
    response = login(client)
    assert b"Success" in response.data


def test_login_fail(client):
    response = client.post("/login", data={
        "username": "user",
        "password": "wrong"
    }, follow_redirects=True)
    assert b"Wrogn login or password" in response.data


def test_redirect_after_login(client):
    response = client.get("/secret")
    assert response.status_code == 302

    response = login(client)
    assert b"Main Page" in response.data


def test_secret_access_authenticated(client):
    login(client)
    response = client.get("/secret")
    assert response.status_code == 200


def test_secret_requires_login(client):
    response = client.get("/secret", follow_redirects=True)
    assert b"You need to aunthethicate to get access" in response.data


def test_redirect_to_secret_after_login(client):
    response = client.get("/secret")
    login(client)
    response = client.get("/secret")
    assert b"Secret Page" in response.data


def test_remember_me(client):
     with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = client.post("/login", data={
            "username": "user",
            "password": "qwerty",
            "remember": "on"
        }, follow_redirects=False)

        cookies = response.headers.getlist("Set-Cookie")

        assert any("remember_token" in c for c in cookies)


def test_navbar_for_guest(client):
    response = client.get("/")
    assert b"Log in" in response.data
    assert b"Secret" not in response.data


def test_navbar_for_user(client):
    login(client)
    response = client.get("/")
    assert b"Secret" in response.data
    assert b"Log in" not in response.data
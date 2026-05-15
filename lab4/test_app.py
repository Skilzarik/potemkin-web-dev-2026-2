import pytest, warnings
from app import app, db, User, Role
from werkzeug.security import generate_password_hash
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# =========================
# HELPERS
# =========================

def text(resp):
    return resp.data.decode("utf-8")


def login(client):
    r = client.post("/login", data={
        "login": "user",
        "password": "qwerty"
    }, follow_redirects=True)

    assert "Вход выполнен" in text(r)
    return r


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test"

    with app.test_client() as client:
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

            role_user = Role(name="User", description="Test user role")
            role_admin = Role(name="Admin", description="Test admin role")
            db.session.add_all([role_user, role_admin])
            db.session.commit()

            user = User(
                login="user",
                password_hash=generate_password_hash("qwerty"),
                first_name="Test",
                role_id=role_user.id
            )
            db.session.add(user)
            db.session.commit()

        yield client



def test_index(client):
    r = client.get("/")
    assert r.status_code == 200


def test_login_success(client):
    r = login(client)
    assert r.status_code == 200


def test_login_fail(client):
    r = client.post("/login", data={
        "login": "wrong",
        "password": "wrong"
    }, follow_redirects=True)

    assert "Ошибка входа" in text(r)


def test_logout(client):
    login(client)
    r = client.get("/logout", follow_redirects=True)
    assert r.status_code == 200


def test_view_user(client):
    r = client.get("/users/1")
    assert r.status_code == 200
    assert "Test" in text(r)


def test_create_requires_login(client):
    r = client.get("/users/create")
    assert r.status_code == 302


def test_create_user(client):
    login(client)

    r = client.post("/users/create", data={
        "login": "test123",
        "password": "Password1!",
        "first_name": "Ivan",
        "last_name": "Petrov",
        "middle_name": "S"
    }, follow_redirects=True)

    assert r.status_code == 200


def test_create_user_validation_fail(client):
    login(client)

    r = client.post("/users/create", data={
        "login": "a",
        "password": "123",
        "first_name": ""
    }, follow_redirects=True)

    assert "Ошибка формы" in text(r)


def test_edit_requires_login(client):
    r = client.get("/users/1/edit")
    assert r.status_code == 302


def test_edit_user(client):
    login(client)

    r = client.post("/users/1/edit", data={
        "first_name": "Updated",
        "last_name": "New",
        "middle_name": "M"
    }, follow_redirects=True)

    assert r.status_code == 200

    with app.app_context():
        user = User.query.get(1)
        assert user.first_name == "Updated"


def test_delete_requires_login(client):
    r = client.post("/users/1/delete")
    assert r.status_code == 302


def test_delete_user(client):
    login(client)

    r = client.post("/users/1/delete", follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        assert User.query.get(1) is None




def test_change_password(client):
    login(client)

    r = client.post("/change-password", data={
        "old": "qwerty",
        "new": "Password1!",
        "repeat": "Password1!"
    }, follow_redirects=True)

    assert r.status_code == 200
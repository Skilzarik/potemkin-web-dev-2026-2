from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re

from models import db, User, Role

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SECRET_KEY"] = "secret"

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Авторизуйтесь"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



def validate_login(login):
    if not login:
        return "Логин пуст"
    if len(login) < 5:
        return "Минимум 5 символов"
    if not re.match(r"^[a-zA-Z0-9]+$", login):
        return "Только латиница и цифры"
    return None


def validate_password(password):
    if len(password) < 8 or len(password) > 128:
        return "Длина 8-128 символов"

    if " " in password:
        return "Без пробелов"

    if not re.search(r"[A-Z]", password):
        return "Нет заглавной буквы"

    if not re.search(r"[a-z]", password):
        return "Нет строчной буквы"

    if not re.search(r"\d", password):
        return "Нет цифры"
    
    if not re.search(r"[~!?@#\$%\^&\*\_\-\+\(\)\[\]\{\}<>\/\\\|\"'\.,:;]", password):
        return "Нужен хотя бы 1 спецсимвол"

    allowed = r"^[A-Za-zА-Яа-я0-9~!?@#\$%\^&\*\_\-\+\(\)\[\]\{\}<>\/\\\|\"'\.,:;]+$"

    if not re.match(allowed, password):
        return "Недопустимые символы в пароле"

    return None



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(login=request.form["login"]).first()

        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            flash("Вход выполнен")
            return redirect(url_for("index"))
        else:
            flash("Ошибка входа")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/")
def index():
    return render_template("index.html", users=User.query.all())


@app.route("/users/<int:id>")
def view_user(id):
    return render_template("user_view.html", user=User.query.get_or_404(id))


@app.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    roles = Role.query.all()

    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]

        errors = {}

        err = validate_login(login)
        if err:
            errors["login"] = err

        err = validate_password(password)
        if err:
            errors["password"] = err

        if not request.form["first_name"]:
            errors["first_name"] = "Введите имя"

        if errors:
            flash("Ошибка формы")
            return render_template("user_form.html", roles=roles, errors=errors)
        default_role = Role.query.filter_by(name="User").first()
        user = User(
            login=login,
            password_hash=generate_password_hash(password),
            first_name=request.form["first_name"],
            last_name=request.form.get("last_name"),
            middle_name=request.form.get("middle_name"),
            role_id=default_role.id if default_role else None
        )

        db.session.add(user)
        db.session.commit()

        flash("Создано")
        return redirect(url_for("index"))

    return render_template("user_form.html", user=None, roles=roles, errors={})


@app.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    roles = Role.query.all()

    if request.method == "POST":
        user.first_name = request.form["first_name"]
        user.last_name = request.form.get("last_name")
        user.middle_name = request.form.get("middle_name")
        user.role_id = request.form.get("role_id") or None

        db.session.commit()
        flash("Обновлено")
        return redirect(url_for("index"))

    return render_template("user_form.html", user=user, roles=roles, errors={})


@app.route("/users/<int:id>/delete", methods=["POST"])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    flash("Удалено")
    return redirect(url_for("index"))

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        if not check_password_hash(current_user.password_hash, request.form["old"]):
            flash("Старый пароль неверный")
            return redirect(url_for("change_password"))

        if request.form["new"] != request.form["repeat"]:
            flash("Пароли не совпадают")
            return redirect(url_for("change_password"))

        err = validate_password(request.form["new"])
        if err:
            flash(err)
            return redirect(url_for("change_password"))

        current_user.password_hash = generate_password_hash(request.form["new"])
        db.session.commit()

        flash("Пароль изменён")
        return redirect(url_for("index"))

    return render_template("change_password.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            db.session.add(Role(name="User", description="Пользователь"))
            db.session.add(Role(name="Admin", description="Администратор"))
            db.session.commit()
        if not User.query.filter_by(login="user").first():
            u = User(
                login="user",
                password_hash=generate_password_hash("qwerty"),
                first_name="Admin",
                role_id=Role.query.filter_by(name="Admin").first().id
            )
            db.session.add(u)
            db.session.commit()

    app.run(debug=True)
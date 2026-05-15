from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "You need to aunthethicate to get access"

# фиктивная БД
users = {
    "user": User("user", "qwerty")
}


@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/counter")
def counter():
    if "visits" not in session:
        session["visits"] = 0
    session["visits"] += 1

    return render_template("counter.html", visits=session["visits"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = bool(request.form.get("remember"))

        user = users.get(username)

        if user and user.password == password:
            login_user(user, remember=remember)
            flash("Success")

            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        else:
            flash("Wrogn login or password")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы")
    return redirect(url_for("index"))


@app.route("/secret")
@login_required
def secret():
    return render_template("secret.html")


if __name__ == "__main__":
    app.run(debug=True)
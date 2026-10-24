import os

from flask import Flask, render_template, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect

from models import db, Usuario
from forms import CadastroForm, LoginForm


app = Flask(__name__)

# Configurações
app.config["SECRET_KEY"] = os.environ.get("AGROGEST_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agrogest.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if not app.config["SECRET_KEY"]:
    raise RuntimeError("Configure a variável AGROGEST_SECRET_KEY.")

# Inicialização das extensões
db.init_app(app)
CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar esta página."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def carregar_usuario(usuario_id):
    return db.session.get(Usuario, int(usuario_id))


# Página inicial
@app.route("/")
def inicio():
    return render_template("index.html")


# Cadastro de usuário
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    form = CadastroForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        usuario_existente = Usuario.query.filter_by(email=email).first()

        if usuario_existente:
            flash("Este e-mail já está cadastrado.", "danger")
            return render_template("cadastro.html", form=form)

        usuario = Usuario(
            nome=form.nome.data.strip(),
            email=email,
            perfil="fornecedor"
        )

        usuario.definir_senha(form.senha.data)

        db.session.add(usuario)
        db.session.commit()

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("cadastro.html", form=form)


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(form.senha.data):
            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("inicio"))

        flash("E-mail ou senha incorretos.", "danger")

    return render_template("login.html", form=form)


# Logout
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("inicio"))


# Criação inicial das tabelas
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )

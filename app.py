import os
from functools import wraps

import click
from flask import (
    Flask, render_template, redirect,
    url_for, flash, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect

from models import db, Usuario, Fornecedor
from forms import CadastroForm, LoginForm, FornecedorForm


app = Flask(__name__)

# Configurações
app.config["SECRET_KEY"] = os.environ.get("AGROGEST_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agrogest.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if not app.config["SECRET_KEY"]:
    raise RuntimeError("Configure AGROGEST_SECRET_KEY.")

# Extensões
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


# Controle de acesso administrativo
def somente_proprietario(funcao):
    @wraps(funcao)
    @login_required
    def protegida(*args, **kwargs):
        if current_user.perfil != "proprietario":
            abort(403)

        return funcao(*args, **kwargs)

    return protegida


# Página inicial
@app.route("/")
def inicio():
    return render_template("index.html")


# Cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    form = CadastroForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        existente = Usuario.query.filter_by(email=email).first()

        if existente:
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

        flash("Cadastro realizado! Faça login.", "success")
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


# Lista de fornecedores
@app.route("/fornecedores")
@somente_proprietario
def listar_fornecedores():
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()

    return render_template(
        "fornecedores.html",
        fornecedores=fornecedores
    )


# Cadastro de fornecedor
@app.route("/fornecedores/novo", methods=["GET", "POST"])
@somente_proprietario
def novo_fornecedor():
    form = FornecedorForm()

    if form.validate_on_submit():
        documento = form.cpf_cnpj.data.strip() or None

        if documento and Fornecedor.query.filter_by(cpf_cnpj=documento).first():
            flash("Este CPF/CNPJ já está cadastrado.", "danger")
            return render_template(
                "form_fornecedor.html",
                form=form,
                titulo="Novo fornecedor"
            )

        fornecedor = Fornecedor(
            nome=form.nome.data.strip(),
            telefone=form.telefone.data.strip() or None,
            cpf_cnpj=documento
        )

        db.session.add(fornecedor)
        db.session.commit()

        flash("Fornecedor cadastrado com sucesso!", "success")
        return redirect(url_for("listar_fornecedores"))

    return render_template(
        "form_fornecedor.html",
        form=form,
        titulo="Novo fornecedor"
    )


# Editar fornecedor
@app.route("/fornecedores/<int:id>/editar", methods=["GET", "POST"])
@somente_proprietario
def editar_fornecedor(id):
    fornecedor = db.get_or_404(Fornecedor, id)
    form = FornecedorForm(obj=fornecedor)

    if form.validate_on_submit():
        documento = form.cpf_cnpj.data.strip() or None

        if documento:
            existente = Fornecedor.query.filter(
                Fornecedor.cpf_cnpj == documento,
                Fornecedor.id != id
            ).first()

            if existente:
                flash("Este CPF/CNPJ já pertence a outro fornecedor.", "danger")
                return render_template(
                    "form_fornecedor.html",
                    form=form,
                    titulo="Editar fornecedor"
                )

        fornecedor.nome = form.nome.data.strip()
        fornecedor.telefone = form.telefone.data.strip() or None
        fornecedor.cpf_cnpj = documento

        db.session.commit()

        flash("Fornecedor atualizado com sucesso!", "success")
        return redirect(url_for("listar_fornecedores"))

    return render_template(
        "form_fornecedor.html",
        form=form,
        titulo="Editar fornecedor"
    )


# Ativar ou desativar fornecedor
@app.route("/fornecedores/<int:id>/situacao", methods=["POST"])
@somente_proprietario
def alterar_situacao_fornecedor(id):
    fornecedor = db.get_or_404(Fornecedor, id)

    fornecedor.ativo = not fornecedor.ativo

    db.session.commit()

    flash("Situação do fornecedor atualizada!", "success")
    return redirect(url_for("listar_fornecedores"))


# Comando administrativo
@app.cli.command("criar-proprietario")
@click.option("--nome", prompt="Nome completo")
@click.option("--email", prompt="E-mail")
@click.password_option("--senha", confirmation_prompt=True)
def criar_proprietario(nome, email, senha):
    email = email.strip().lower()

    if Usuario.query.filter_by(perfil="proprietario").first():
        click.echo("Já existe uma conta de proprietário.")
        return

    if Usuario.query.filter_by(email=email).first():
        click.echo("Este e-mail já está cadastrado.")
        return

    if len(nome.strip()) < 3 or len(senha) < 8:
        click.echo("Nome ou senha fora dos requisitos mínimos.")
        return

    usuario = Usuario(
        nome=nome.strip(),
        email=email,
        perfil="proprietario"
    )

    usuario.definir_senha(senha)

    db.session.add(usuario)
    db.session.commit()

    click.echo("Proprietário cadastrado com sucesso!")


# Cria tabelas inexistentes
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")


"""Aplicação independente para testes; nunca abre instance/agrogest.db."""

import pytest
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from models import db, Usuario, Fornecedor, Entrega  # noqa: F401
from estoque import estoque_bp  # Também registra os modelos de estoque
from pagamentos import pagamentos_bp
from portal_fornecedor import portal_bp


@pytest.fixture
def app(tmp_path):
    aplicativo = Flask(
        __name__,
        template_folder="../templates"
    )

    aplicativo.config.update(
        TESTING=True,
        SECRET_KEY="chave-apenas-para-testes",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'teste.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
    )

    # Banco de dados temporário
    db.init_app(aplicativo)

    # Registra csrf_token() nos templates.
    # A validação CSRF fica desabilitada SOMENTE nos testes.
    CSRFProtect(aplicativo)

    # Autenticação
    login_manager = LoginManager()
    login_manager.init_app(aplicativo)

    @login_manager.user_loader
    def carregar_usuario(usuario_id):
        return db.session.get(Usuario, int(usuario_id))

    # Endpoints de navegação usados pelo base.html nos testes.
    for endpoint, caminho in [
        ("inicio", "/"),
        ("login", "/login"),
        ("cadastro", "/cadastro"),
        ("logout", "/logout"),
        ("listar_fornecedores", "/fornecedores"),
        ("listar_entregas", "/entregas"),
    ]:
        aplicativo.add_url_rule(
            caminho,
            endpoint=endpoint,
            view_func=lambda: "Apenas navegacao de testes",
        )

    aplicativo.register_blueprint(estoque_bp)
    aplicativo.register_blueprint(pagamentos_bp)
    aplicativo.register_blueprint(portal_bp)

    with aplicativo.app_context():
        db.create_all()

        yield aplicativo

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def criar_usuario(perfil, nome, email):
    usuario = Usuario(
        nome=nome,
        email=email,
        perfil=perfil
    )

    usuario.definir_senha("SenhaDeTeste123!")

    db.session.add(usuario)
    db.session.commit()

    return usuario


def autenticar(client, usuario):
    # Login somente dentro do cliente de teste.
    # Não existe rota pública de teste.
    with client.session_transaction() as sessao:
        sessao["_user_id"] = str(usuario.id)
        sessao["_fresh"] = True

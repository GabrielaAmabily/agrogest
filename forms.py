from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp


class CadastroForm(FlaskForm):
    nome = StringField(
        "Nome completo",
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    email = StringField(
        "E-mail",
        validators=[
            DataRequired(),
            Length(max=120),
            Regexp(
                r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
                message="Informe um e-mail válido."
            )
        ]
    )

    senha = PasswordField(
        "Senha",
        validators=[DataRequired(), Length(min=8)]
    )

    confirmar_senha = PasswordField(
        "Confirmar senha",
        validators=[
            DataRequired(),
            EqualTo("senha", message="As senhas não coincidem.")
        ]
    )

    enviar = SubmitField("Criar conta")


class LoginForm(FlaskForm):
    email = StringField(
        "E-mail",
        validators=[DataRequired()]
    )

    senha = PasswordField(
        "Senha",
        validators=[DataRequired()]
    )

    enviar = SubmitField("Entrar")

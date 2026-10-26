
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    SelectField, DateField, IntegerField,
    DecimalField, TextAreaField
)
from wtforms.validators import (
    DataRequired, Length, EqualTo,
    Regexp, Optional, NumberRange
)


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
    email = StringField("E-mail", validators=[DataRequired()])
    senha = PasswordField("Senha", validators=[DataRequired()])
    enviar = SubmitField("Entrar")


class FornecedorForm(FlaskForm):
    nome = StringField(
        "Nome do fornecedor",
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    telefone = StringField(
        "Telefone",
        validators=[Optional(), Length(max=20)]
    )

    cpf_cnpj = StringField(
        "CPF ou CNPJ (opcional)",
        validators=[Optional(), Length(max=18)]
    )

    enviar = SubmitField("Salvar fornecedor")


class EntregaForm(FlaskForm):
    fornecedor_id = SelectField(
        "Fornecedor",
        coerce=int,
        validators=[DataRequired()]
    )

    data = DateField(
        "Data da entrega",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    quantidade_caixas = IntegerField(
        "Quantidade de caixas",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="Informe ao menos uma caixa.")
        ]
    )

    valor_unitario = DecimalField(
        "Valor unitário (R$)",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Informe um valor positivo.")
        ]
    )

    observacoes = TextAreaField(
        "Observações",
        validators=[Optional(), Length(max=500)]
    )

    enviar = SubmitField("Salvar entrega")

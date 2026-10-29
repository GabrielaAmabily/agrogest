
from decimal import Decimal
from functools import wraps

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, abort
)
from flask_login import login_required, current_user

from models import db, Usuario, Fornecedor, Entrega


portal_bp = Blueprint("portal", __name__)


def exigir_perfil(perfil):
    def decorador(funcao):
        @wraps(funcao)
        @login_required
        def protegida(*args, **kwargs):
            if current_user.perfil != perfil:
                abort(403)
            return funcao(*args, **kwargs)
        return protegida
    return decorador


# Proprietário vincula uma conta ao fornecedor
@portal_bp.route(
    "/fornecedores/<int:id>/vincular",
    methods=["GET", "POST"]
)
@exigir_perfil("proprietario")
def vincular_fornecedor(id):
    fornecedor = db.get_or_404(Fornecedor, id)

    # Contas já vinculadas a outros fornecedores
    ids_vinculados = [
        item.usuario_id
        for item in Fornecedor.query.filter(
            Fornecedor.usuario_id.isnot(None),
            Fornecedor.id != fornecedor.id
        ).all()
    ]

    consulta = Usuario.query.filter_by(perfil="fornecedor")

    if ids_vinculados:
        consulta = consulta.filter(
            ~Usuario.id.in_(ids_vinculados)
        )

    usuarios_disponiveis = consulta.order_by(Usuario.nome).all()

    if request.method == "POST":
        usuario_texto = request.form.get("usuario_id", "").strip()

        if not usuario_texto:
            fornecedor.usuario_id = None
            db.session.commit()

            flash("Vínculo removido com sucesso.", "success")
            return redirect(url_for("listar_fornecedores"))

        try:
            usuario_id = int(usuario_texto)
        except ValueError:
            abort(400)

        usuario = db.session.get(Usuario, usuario_id)

        if not usuario or usuario.perfil != "fornecedor":
            abort(400)

        outro_vinculo = Fornecedor.query.filter(
            Fornecedor.usuario_id == usuario.id,
            Fornecedor.id != fornecedor.id
        ).first()

        if outro_vinculo:
            flash(
                "Esta conta já pertence a outro fornecedor.",
                "danger"
            )
        else:
            fornecedor.usuario_id = usuario.id
            db.session.commit()

            flash("Conta vinculada com sucesso!", "success")
            return redirect(url_for("listar_fornecedores"))

    return render_template(
        "vincular_fornecedor.html",
        fornecedor=fornecedor,
        usuarios=usuarios_disponiveis
    )


# Área de consulta do fornecedor autenticado
@portal_bp.route("/minhas-entregas")
@exigir_perfil("fornecedor")
def minhas_entregas():
    fornecedor = Fornecedor.query.filter_by(
        usuario_id=current_user.id
    ).first()

    if fornecedor is None:
        return render_template(
            "minhas_entregas.html",
            fornecedor=None,
            entregas=[],
            total_pendente=Decimal("0.00"),
            total_pago=Decimal("0.00")
        )

    entregas = (
        Entrega.query
        .filter_by(fornecedor_id=fornecedor.id)
        .order_by(Entrega.data.desc(), Entrega.id.desc())
        .all()
    )

    total_pendente = sum(
        (
            entrega.valor_total
            for entrega in entregas
            if entrega.situacao == "nao_paga"
        ),
        Decimal("0.00")
    )

    total_pago = sum(
        (
            entrega.valor_total
            for entrega in entregas
            if entrega.situacao == "paga"
        ),
        Decimal("0.00")
    )

    return render_template(
        "minhas_entregas.html",
        fornecedor=fornecedor,
        entregas=entregas,
        total_pendente=total_pendente,
        total_pago=total_pago
    )


from datetime import date
from decimal import Decimal
from functools import wraps
from io import BytesIO
from xml.sax.saxutils import escape

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, abort, send_file
)
from flask_login import login_required, current_user
from sqlalchemy import update

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table,
    TableStyle, Spacer
)

from models import db, Fornecedor, Entrega


pagamentos_bp = Blueprint("pagamentos", __name__)


def somente_proprietario(funcao):
    @wraps(funcao)
    @login_required
    def protegida(*args, **kwargs):
        if current_user.perfil != "proprietario":
            abort(403)
        return funcao(*args, **kwargs)
    return protegida


def moeda(valor):
    texto = f"{Decimal(str(valor)):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


# Interpreta filtros opcionais
def obter_filtros(dados):
    fornecedor_texto = dados.get("fornecedor_id", "").strip()
    situacao = dados.get("situacao", "nao_paga").strip()
    inicio_texto = dados.get("data_inicio", "").strip()
    fim_texto = dados.get("data_fim", "").strip()

    if situacao not in ("nao_paga", "paga", "todas"):
        raise ValueError("Situação de pagamento inválida.")

    fornecedor_id = None

    if fornecedor_texto:
        try:
            fornecedor_id = int(fornecedor_texto)
        except ValueError:
            raise ValueError("Fornecedor inválido.")

        if fornecedor_id <= 0 or not db.session.get(Fornecedor, fornecedor_id):
            raise ValueError("Fornecedor não encontrado.")

    try:
        inicio = date.fromisoformat(inicio_texto) if inicio_texto else None
        fim = date.fromisoformat(fim_texto) if fim_texto else None
    except ValueError:
        raise ValueError("Informe datas válidas.")

    if inicio and fim and inicio > fim:
        raise ValueError("A data inicial não pode ser posterior à final.")

    return {
        "fornecedor_id": fornecedor_id,
        "situacao": situacao,
        "data_inicio": inicio,
        "data_fim": fim
    }


def consultar_entregas(filtros):
    consulta = Entrega.query

    if filtros["fornecedor_id"] is not None:
        consulta = consulta.filter(
            Entrega.fornecedor_id == filtros["fornecedor_id"]
        )

    if filtros["situacao"] != "todas":
        consulta = consulta.filter(
            Entrega.situacao == filtros["situacao"]
        )

    if filtros["data_inicio"]:
        consulta = consulta.filter(
            Entrega.data >= filtros["data_inicio"]
        )

    if filtros["data_fim"]:
        consulta = consulta.filter(
            Entrega.data <= filtros["data_fim"]
        )

    return consulta


def calcular_totais(entregas):
    pendente = sum(
        (e.valor_total for e in entregas if e.situacao == "nao_paga"),
        Decimal("0.00")
    )

    pago = sum(
        (e.valor_total for e in entregas if e.situacao == "paga"),
        Decimal("0.00")
    )

    return pendente, pago


def parametros_url(filtros):
    return {
        "fornecedor_id": filtros["fornecedor_id"] or "",
        "situacao": filtros["situacao"],
        "data_inicio": (
            filtros["data_inicio"].isoformat()
            if filtros["data_inicio"] else ""
        ),
        "data_fim": (
            filtros["data_fim"].isoformat()
            if filtros["data_fim"] else ""
        )
    }


# Página principal de pagamentos
@pagamentos_bp.route("/pagamentos")
@somente_proprietario
def listar_pagamentos():
    try:
        filtros = obter_filtros(request.args)
    except ValueError as erro:
        flash(str(erro), "warning")
        return redirect(url_for("pagamentos.listar_pagamentos"))

    entregas = (
        consultar_entregas(filtros)
        .order_by(Entrega.data.desc(), Entrega.id.desc())
        .all()
    )

    total_pendente, total_pago = calcular_totais(entregas)

    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()

    return render_template(
        "pagamentos.html",
        entregas=entregas,
        fornecedores=fornecedores,
        filtros=parametros_url(filtros),
        total_pendente=total_pendente,
        total_pago=total_pago
    )


# Confirma as entregas selecionadas
@pagamentos_bp.route("/pagamentos/confirmar", methods=["POST"])
@somente_proprietario
def confirmar_pagamentos():
    try:
        filtros = obter_filtros(request.form)
    except ValueError as erro:
        flash(str(erro), "danger")
        return redirect(url_for("pagamentos.listar_pagamentos"))

    ids_recebidos = request.form.getlist("entrega_ids")

    try:
        ids = [int(valor) for valor in ids_recebidos]
    except ValueError:
        abort(400)

    if not ids or any(i <= 0 for i in ids) or len(ids) != len(set(ids)):
        flash("Selecione entregas válidas.", "warning")
        return redirect(url_for(
            "pagamentos.listar_pagamentos",
            **parametros_url(filtros)
        ))

    # Confere se todas as entregas selecionadas
    # correspondem aos filtros e ainda estão pendentes.
    consulta = consultar_entregas(filtros).filter(
        Entrega.id.in_(ids),
        Entrega.situacao == "nao_paga"
    )

    if consulta.count() != len(ids):
        flash("Seleção inválida. Atualize a consulta.", "danger")
        return redirect(url_for(
            "pagamentos.listar_pagamentos",
            **parametros_url(filtros)
        ))

    # Atualização única e condicionada no banco
    resultado = db.session.execute(
        update(Entrega)
        .where(
            Entrega.id.in_(ids),
            Entrega.situacao == "nao_paga"
        )
        .values(situacao="paga")
    )

    if resultado.rowcount != len(ids):
        db.session.rollback()
        flash("O pagamento não foi registrado. Tente novamente.", "danger")
    else:
        db.session.commit()
        flash(
            f"{len(ids)} entrega(s) marcada(s) como paga(s)!",
            "success"
        )

    return redirect(url_for(
        "pagamentos.listar_pagamentos",
        **parametros_url(filtros)
    ))


# Relatório PDF de acordo com os filtros
@pagamentos_bp.route("/pagamentos/pdf")
@somente_proprietario
def gerar_pdf():
    try:
        filtros = obter_filtros(request.args)
    except ValueError as erro:
        flash(str(erro), "danger")
        return redirect(url_for("pagamentos.listar_pagamentos"))

    entregas = (
        consultar_entregas(filtros)
        .order_by(Entrega.fornecedor_id, Entrega.data, Entrega.id)
        .all()
    )

    if not entregas:
        flash("Não existem entregas para gerar o relatório.", "warning")
        return redirect(url_for(
            "pagamentos.listar_pagamentos",
            **parametros_url(filtros)
        ))

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(
        Paragraph("AgroGest - Relatório de Pagamentos", estilos["Title"])
    )
    elementos.append(Spacer(1, 0.4 * cm))

    if filtros["fornecedor_id"]:
        fornecedor = db.session.get(
            Fornecedor, filtros["fornecedor_id"]
        )
        nome_fornecedor = fornecedor.nome
    else:
        nome_fornecedor = "Todos os fornecedores"

    inicio = (
        filtros["data_inicio"].strftime("%d/%m/%Y")
        if filtros["data_inicio"] else "Sem limite"
    )

    fim = (
        filtros["data_fim"].strftime("%d/%m/%Y")
        if filtros["data_fim"] else "Sem limite"
    )

    situacoes = {
        "nao_paga": "Pendentes",
        "paga": "Pagas",
        "todas": "Todas"
    }

    elementos.append(
        Paragraph(
            f"Fornecedores: {escape(nome_fornecedor)}",
            estilos["Normal"]
        )
    )
    elementos.append(
        Paragraph(
            f"Período: {inicio} até {fim}",
            estilos["Normal"]
        )
    )
    elementos.append(
        Paragraph(
            f"Situação: {situacoes[filtros['situacao']]}",
            estilos["Normal"]
        )
    )
    elementos.append(Spacer(1, 0.5 * cm))

    dados = [[
        "Fornecedor", "Data", "Caixas", "Unitário", "Total", "Situação"
    ]]

    for entrega in entregas:
        dados.append([
            Paragraph(
                escape(entrega.fornecedor.nome),
                estilos["Normal"]
            ),
            entrega.data.strftime("%d/%m/%Y"),
            str(entrega.quantidade_caixas),
            moeda(entrega.valor_unitario),
            moeda(entrega.valor_total),
            "Paga" if entrega.situacao == "paga" else "Pendente"
        ])

    tabela = Table(
        dados,
        colWidths=[
            4.0 * cm, 2.5 * cm, 1.6 * cm,
            3.1 * cm, 3.1 * cm, 2.5 * cm
        ],
        repeatRows=1,
        hAlign="LEFT"
    )

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#246B45")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#F6F8F3")
        ]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 0.6 * cm))

    total_pendente, total_pago = calcular_totais(entregas)

    elementos.append(
        Paragraph(
            f"Total pendente: {moeda(total_pendente)}",
            estilos["Heading3"]
        )
    )
    elementos.append(
        Paragraph(
            f"Total pago: {moeda(total_pago)}",
            estilos["Heading3"]
        )
    )
    elementos.append(
        Paragraph(
            f"Total geral: {moeda(total_pendente + total_pago)}",
            estilos["Heading2"]
        )
    )

    documento.build(elementos)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="agrogest_relatorio_pagamentos.pdf",
        mimetype="application/pdf"
    )

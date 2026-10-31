"""Testes iniciais sem conexão com o banco de produção."""
from datetime import date, timedelta
from decimal import Decimal

from models import db, Fornecedor, Entrega
from estoque import Insumo, LoteEstoque, MovimentacaoEstoque
from conftest import autenticar, criar_usuario


def criar_insumo(nome="Fertilizante A", minimo=10, categoria="Fertilizante"):
    insumo = Insumo(
        nome=nome, categoria=categoria, unidade="kg", estoque_minimo=minimo
    )
    db.session.add(insumo)
    db.session.commit()
    return insumo


def criar_proprietario(client):
    usuario = criar_usuario("proprietario", "Proprietario Teste", "dono@teste.local")
    autenticar(client, usuario)
    return usuario


def test_total_entrega_e_bloqueio_apos_pagamento(app):
    fornecedor = Fornecedor(nome="Fornecedor A", ativo=True)
    db.session.add(fornecedor)
    db.session.flush()
    entrega = Entrega(
        fornecedor_id=fornecedor.id,
        data=date.today(),
        quantidade_caixas=148,
        valor_unitario=Decimal("24.00"),
        situacao="nao_paga",
    )
    db.session.add(entrega)
    db.session.commit()

    assert entrega.valor_total == Decimal("3552.00")
    assert entrega.pode_editar is True
    entrega.situacao = "paga"
    db.session.commit()
    assert entrega.pode_editar is False


def test_entrada_saida_e_historico(app, client):
    criar_proprietario(client)
    insumo = criar_insumo()

    resposta = client.post(
        f"/estoque/{insumo.id}/entrada",
        data={"quantidade": "20", "validade": "", "observacao": "Compra"},
    )
    assert resposta.status_code == 302
    db.session.refresh(insumo)
    assert insumo.quantidade_disponivel == 20

    resposta = client.post(
        f"/estoque/{insumo.id}/saida",
        data={"quantidade": "5", "observacao": "Utilizacao"},
    )
    assert resposta.status_code == 302
    db.session.expire_all()
    assert db.session.get(Insumo, insumo.id).quantidade_disponivel == 15
    assert MovimentacaoEstoque.query.filter_by(insumo_id=insumo.id).count() == 2


def test_saida_acima_do_saldo_nao_altera_estoque(app, client):
    criar_proprietario(client)
    insumo = criar_insumo()
    db.session.add(LoteEstoque(insumo_id=insumo.id, quantidade_atual=8))
    db.session.commit()

    resposta = client.post(
        f"/estoque/{insumo.id}/saida",
        data={"quantidade": "20", "observacao": "Tentativa"},
    )
    assert resposta.status_code == 200  # formulário com alerta, sem movimentação
    db.session.expire_all()
    assert db.session.get(Insumo, insumo.id).quantidade_disponivel == 8
    assert MovimentacaoEstoque.query.count() == 0


def test_lote_vencido_nao_pode_ser_consumido(app, client):
    criar_proprietario(client)
    insumo = criar_insumo()
    db.session.add_all([
        LoteEstoque(
            insumo_id=insumo.id, quantidade_atual=10,
            validade=date.today() - timedelta(days=1),
        ),
        LoteEstoque(
            insumo_id=insumo.id, quantidade_atual=6,
            validade=date.today() + timedelta(days=30),
        ),
    ])
    db.session.commit()

    assert insumo.quantidade_total == 16
    assert insumo.quantidade_vencida == 10
    assert insumo.quantidade_disponivel == 6

    resposta = client.post(
        f"/estoque/{insumo.id}/saida",
        data={"quantidade": "8", "observacao": "Nao permitida"},
    )
    assert resposta.status_code == 200
    assert insumo.quantidade_disponivel == 6


def test_fornecedor_nao_acessa_estoque(app, client):
    fornecedor_usuario = criar_usuario(
        "fornecedor", "Usuario Fornecedor", "fornecedor@teste.local"
    )
    autenticar(client, fornecedor_usuario)
    assert client.get("/estoque").status_code == 403
    assert client.get("/estoque/historico").status_code == 403


def test_fornecedor_nao_acessa_pagamentos(app, client):
    fornecedor_usuario = criar_usuario(
        "fornecedor", "Usuario Fornecedor", "fornecedor2@teste.local"
    )
    autenticar(client, fornecedor_usuario)
    assert client.get("/pagamentos").status_code == 403
    assert client.get("/pagamentos/pdf").status_code == 403

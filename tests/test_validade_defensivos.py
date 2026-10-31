"""Regressão: um defensivo não pode manter saldo sem validade."""
from datetime import date, timedelta

from models import db
from estoque import Insumo, LoteEstoque
from conftest import autenticar, criar_usuario


def test_impede_transformar_em_defensivo_com_lote_sem_validade(app, client):
    usuario = criar_usuario('proprietario', 'Proprietario Teste', 'dono-validade@teste.local')
    autenticar(client, usuario)

    insumo = Insumo(nome='Produto A', categoria='Fertilizante',
                    unidade='kg', estoque_minimo=5)
    db.session.add(insumo)
    db.session.flush()
    db.session.add(LoteEstoque(insumo_id=insumo.id, quantidade_atual=10, validade=None))
    db.session.commit()

    resposta = client.post(f'/estoque/{insumo.id}/editar', data={
        'nome': 'Produto A', 'categoria': 'Defensivo',
        'unidade': 'kg', 'estoque_minimo': '5'
    })

    assert resposta.status_code == 200
    db.session.refresh(insumo)
    assert insumo.categoria == 'Fertilizante'
    assert insumo.quantidade_disponivel == 10


def test_permite_defensivo_quando_todos_lotes_ativos_tem_validade(app, client):
    usuario = criar_usuario('proprietario', 'Proprietario Teste', 'dono-validade2@teste.local')
    autenticar(client, usuario)

    insumo = Insumo(nome='Produto B', categoria='Fertilizante',
                    unidade='kg', estoque_minimo=5)
    db.session.add(insumo)
    db.session.flush()
    db.session.add_all([
        LoteEstoque(insumo_id=insumo.id, quantidade_atual=0, validade=None),
        LoteEstoque(insumo_id=insumo.id, quantidade_atual=8,
                    validade=date.today() + timedelta(days=90))
    ])
    db.session.commit()

    resposta = client.post(f'/estoque/{insumo.id}/editar', data={
        'nome': 'Produto B', 'categoria': 'Defensivo',
        'unidade': 'kg', 'estoque_minimo': '5'
    })

    assert resposta.status_code == 302
    db.session.refresh(insumo)
    assert insumo.categoria == 'Defensivo'

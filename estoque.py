from datetime import date, datetime, timedelta
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from models import db

estoque_bp = Blueprint('estoque', __name__)
CATEGORIAS = ['Fertilizante', 'Defensivo', 'Embalagem', 'Ferramenta', 'Outro']
UNIDADES = ['un', 'kg', 'L', 'pacote']


class Insumo(db.Model):
    __tablename__ = 'insumos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(40), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    lotes = db.relationship('LoteEstoque', back_populates='insumo')

    @property
    def quantidade_total(self):
        return sum(lote.quantidade_atual for lote in self.lotes)

    @property
    def quantidade_disponivel(self):
        hoje = date.today()
        return sum(lote.quantidade_atual for lote in self.lotes
                   if lote.validade is None or lote.validade >= hoje)

    @property
    def quantidade_vencida(self):
        hoje = date.today()
        return sum(lote.quantidade_atual for lote in self.lotes
                   if lote.validade is not None and lote.validade < hoje)

    @property
    def estoque_baixo(self):
        return self.quantidade_disponivel <= self.estoque_minimo


class LoteEstoque(db.Model):
    __tablename__ = 'lotes_estoque'
    id = db.Column(db.Integer, primary_key=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False, default=0)
    validade = db.Column(db.Date, nullable=True)
    insumo = db.relationship('Insumo', back_populates='lotes')


class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    id = db.Column(db.Integer, primary_key=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=False)
    tipo = db.Column(db.String(12), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data = db.Column(db.DateTime, nullable=False, default=datetime.now)
    observacao = db.Column(db.String(250), nullable=True)
    insumo = db.relationship('Insumo')


def somente_proprietario(funcao):
    @wraps(funcao)
    @login_required
    def protegida(*args, **kwargs):
        if current_user.perfil != 'proprietario':
            abort(403)
        return funcao(*args, **kwargs)
    return protegida


def ler_quantidade(valor, permitir_zero=False):
    try:
        quantidade = int(valor)
    except (TypeError, ValueError):
        return None
    if str(quantidade) != str(valor).strip():
        return None
    minimo = 0 if permitir_zero else 1
    return quantidade if minimo <= quantidade <= 1000000 else None


def validar_formulario_insumo(editar=None):
    nome = request.form.get('nome', '').strip()
    categoria = request.form.get('categoria', '')
    unidade = request.form.get('unidade', '')
    minimo = ler_quantidade(request.form.get('estoque_minimo'), permitir_zero=True)
    if not nome or len(nome) > 120 or categoria not in CATEGORIAS or unidade not in UNIDADES or minimo is None:
        return None, 'Confira o nome, categoria, unidade e estoque mínimo.'
    existente = Insumo.query.filter(func.lower(Insumo.nome) == nome.lower()).first()
    if existente and (editar is None or existente.id != editar.id):
        return None, 'Já existe um insumo com esse nome.'
    return (nome, categoria, unidade, minimo), None


@estoque_bp.route('/estoque')
@somente_proprietario
def listar_estoque():
    insumos = Insumo.query.filter_by(ativo=True).order_by(Insumo.nome).all()
    hoje = date.today()
    limite = hoje + timedelta(days=30)
    lotes_vencidos = LoteEstoque.query.join(Insumo).filter(
        Insumo.ativo.is_(True), LoteEstoque.quantidade_atual > 0,
        LoteEstoque.validade < hoje).all()
    lotes_proximos = LoteEstoque.query.join(Insumo).filter(
        Insumo.ativo.is_(True), LoteEstoque.quantidade_atual > 0,
        LoteEstoque.validade >= hoje, LoteEstoque.validade <= limite).all()
    return render_template('estoque.html', insumos=insumos,
                           estoque_baixo=[i for i in insumos if i.estoque_baixo],
                           lotes_vencidos=lotes_vencidos, lotes_proximos=lotes_proximos)


@estoque_bp.route('/estoque/novo', methods=['GET', 'POST'])
@somente_proprietario
def novo_insumo():
    if request.method == 'POST':
        dados, erro = validar_formulario_insumo()
        if erro:
            flash(erro, 'danger')
        else:
            nome, categoria, unidade, minimo = dados
            db.session.add(Insumo(nome=nome, categoria=categoria,
                                  unidade=unidade, estoque_minimo=minimo))
            db.session.commit()
            flash('Insumo cadastrado com sucesso!', 'success')
            return redirect(url_for('estoque.listar_estoque'))
    return render_template('form_insumo.html', insumo=None, categorias=CATEGORIAS,
                           unidades=UNIDADES)


@estoque_bp.route('/estoque/<int:id>/editar', methods=['GET', 'POST'])
@somente_proprietario
def editar_insumo(id):
    insumo = db.get_or_404(Insumo, id)
    if request.method == 'POST':
        dados, erro = validar_formulario_insumo(editar=insumo)
        if erro:
            flash(erro, 'danger')
        else:
            nome, categoria, unidade, minimo = dados
            # Evita corromper quantidades históricas em unidades distintas.
            if insumo.quantidade_total > 0 and unidade != insumo.unidade:
                flash('Não altere a unidade enquanto houver quantidade em estoque.', 'danger')
            elif (MovimentacaoEstoque.query.filter_by(insumo_id=id).first()
                  and unidade != insumo.unidade):
                flash('A unidade não pode ser alterada após haver movimentações.', 'danger')
            else:
                insumo.nome = nome
                insumo.categoria = categoria
                insumo.unidade = unidade
                insumo.estoque_minimo = minimo
                db.session.commit()
                flash('Insumo atualizado com sucesso!', 'success')
                return redirect(url_for('estoque.listar_estoque'))
    return render_template('form_insumo.html', insumo=insumo, categorias=CATEGORIAS,
                           unidades=UNIDADES)


@estoque_bp.route('/estoque/<int:id>/situacao', methods=['POST'])
@somente_proprietario
def alterar_situacao_insumo(id):
    insumo = db.get_or_404(Insumo, id)
    if insumo.ativo and insumo.quantidade_total > 0:
        flash('Para desativar, primeiro dê baixa no saldo dos lotes.', 'warning')
    else:
        insumo.ativo = not insumo.ativo
        db.session.commit()
        flash('Situação do insumo atualizada.', 'success')
    return redirect(url_for('estoque.listar_estoque'))


@estoque_bp.route('/estoque/inativos')
@somente_proprietario
def listar_inativos():
    insumos = Insumo.query.filter_by(ativo=False).order_by(Insumo.nome).all()
    return render_template('insumos_inativos.html', insumos=insumos)


@estoque_bp.route('/estoque/<int:id>/entrada', methods=['GET', 'POST'])
@somente_proprietario
def registrar_entrada(id):
    insumo = db.get_or_404(Insumo, id)
    if not insumo.ativo:
        abort(404)
    if request.method == 'POST':
        quantidade = ler_quantidade(request.form.get('quantidade'))
        validade_texto = request.form.get('validade', '').strip()
        observacao = request.form.get('observacao', '').strip()
        try:
            validade = date.fromisoformat(validade_texto) if validade_texto else None
        except ValueError:
            flash('Data de validade inválida.', 'danger')
            return render_template('movimentar_estoque.html', insumo=insumo, tipo='entrada')
        if quantidade is None or len(observacao) > 250:
            flash('Confira a quantidade e a observação.', 'danger')
        elif insumo.categoria == 'Defensivo' and not validade:
            flash('Informe a validade do defensivo.', 'danger')
        elif validade is not None and validade < date.today():
            flash('Não é permitido registrar entrada de lote vencido.', 'danger')
        else:
            lote = LoteEstoque(insumo_id=insumo.id, quantidade_atual=quantidade,
                               validade=validade)
            mov = MovimentacaoEstoque(insumo_id=insumo.id, tipo='entrada',
                                      quantidade=quantidade, observacao=observacao or None)
            db.session.add_all([lote, mov])
            db.session.commit()
            flash('Entrada registrada com sucesso!', 'success')
            return redirect(url_for('estoque.listar_estoque'))
    return render_template('movimentar_estoque.html', insumo=insumo, tipo='entrada')


@estoque_bp.route('/estoque/<int:id>/saida', methods=['GET', 'POST'])
@somente_proprietario
def registrar_saida(id):
    insumo = db.get_or_404(Insumo, id)
    if not insumo.ativo:
        abort(404)
    if request.method == 'POST':
        quantidade = ler_quantidade(request.form.get('quantidade'))
        observacao = request.form.get('observacao', '').strip()
        if quantidade is None or len(observacao) > 250:
            flash('Confira a quantidade e a observação.', 'danger')
        elif quantidade > insumo.quantidade_disponivel:
            flash('Estoque insuficiente: lotes vencidos não podem ser utilizados.', 'danger')
        else:
            hoje = date.today()
            lotes = [l for l in insumo.lotes if l.quantidade_atual > 0
                     and (l.validade is None or l.validade >= hoje)]
            lotes.sort(key=lambda l: (l.validade is None, l.validade or date.max, l.id))
            restante = quantidade
            for lote in lotes:
                retirar = min(restante, lote.quantidade_atual)
                lote.quantidade_atual -= retirar
                restante -= retirar
                if restante == 0:
                    break
            db.session.add(MovimentacaoEstoque(
                insumo_id=id, tipo='saida', quantidade=quantidade,
                observacao=observacao or None))
            db.session.commit()
            flash('Saída registrada com sucesso!', 'success')
            return redirect(url_for('estoque.listar_estoque'))
    return render_template('movimentar_estoque.html', insumo=insumo, tipo='saida')


@estoque_bp.route('/estoque/<int:id>/lotes')
@somente_proprietario
def listar_lotes(id):
    insumo = db.get_or_404(Insumo, id)
    lotes = LoteEstoque.query.filter_by(insumo_id=id).order_by(
        LoteEstoque.validade.asc(), LoteEstoque.id.asc()).all()
    return render_template('lotes_estoque.html', insumo=insumo, lotes=lotes,
                           hoje=date.today())


@estoque_bp.route('/estoque/lotes/<int:id>/descartar', methods=['POST'])
@somente_proprietario
def descartar_lote(id):
    lote = db.get_or_404(LoteEstoque, id)
    if lote.quantidade_atual <= 0:
        flash('Este lote já não possui saldo.', 'warning')
    else:
        quantidade = lote.quantidade_atual
        lote.quantidade_atual = 0
        obs = f'Descarte do lote #{lote.id}'
        if lote.validade:
            obs += f' (validade {lote.validade.strftime("%d/%m/%Y")})'
        db.session.add(MovimentacaoEstoque(insumo_id=lote.insumo_id,
                                           tipo='descarte', quantidade=quantidade,
                                           observacao=obs))
        db.session.commit()
        flash('Lote descartado e baixa registrada no histórico.', 'success')
    return redirect(url_for('estoque.listar_lotes', id=lote.insumo_id))


@estoque_bp.route('/estoque/historico')
@somente_proprietario
def historico_estoque():
    movimentos = MovimentacaoEstoque.query.order_by(
        MovimentacaoEstoque.data.desc(), MovimentacaoEstoque.id.desc()).all()
    return render_template('historico_estoque.html', movimentacoes=movimentos)

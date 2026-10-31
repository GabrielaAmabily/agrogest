# 🍓 AgroGest

**Sistema web de gestão de fornecedores, entregas, pagamentos e estoque de insumos para a produção de morangos.**

Projeto acadêmico de **Gabriela Amabily Cézar**, Engenharia de Computação — Universidade Federal de Itajubá (UNIFEI), disciplina **ECOT11A — Laboratório de Engenharia de Software I**.

## Sobre o projeto

O AgroGest centraliza o cadastro de fornecedores, o registro de entregas de morangos e seus valores, o acompanhamento de pagamentos e a movimentação de materiais utilizados na produção.

**Perfis disponíveis:**
- **Proprietário:** gerencia fornecedores, entregas, pagamentos e estoque.
- **Fornecedor:** consulta somente as entregas e pagamentos do cadastro associado à sua conta.

## Funcionalidades

**Fornecedores:** cadastro, consulta e edição; ativação/desativação; prevenção de CPF/CNPJ duplicado; vinculação de conta de acesso.

**Entregas e pagamentos:** data, fornecedor, quantidade de caixas e preço unitário; total calculado automaticamente; filtros por fornecedor, datas e situação; confirmação de pagamentos; bloqueio de edição de entregas pagas pelo fluxo normal; relatórios PDF.

**Estoque de insumos:** cadastro e edição; categorias, unidades e estoque mínimo; entradas separadas por lotes; saídas por ordem de validade; bloqueio de uso de lote vencido e de saída superior ao saldo; alertas de estoque mínimo e vencimentos; consulta e descarte de lotes, histórico de movimentações e inativação de insumos. Defensivos exigem validade e a edição da categoria não pode deixar lotes ativos sem validade.

**Segurança:** senhas armazenadas por hash; controle de acesso por perfil; isolamento das informações de fornecedores; proteção CSRF nos formulários da aplicação.

## Tecnologias

Python 3, Flask, Flask-SQLAlchemy, SQLite, Flask-Login, Flask-WTF, Bootstrap 5, ReportLab, pytest, Git e GitHub.

## Instalação e execução local

Pré-requisitos: Python 3 e Git. O projeto não exige servidor externo de banco de dados. **É obrigatório configurar `AGROGEST_SECRET_KEY` antes de iniciar a aplicação ou executar o comando de criação de proprietário.** Não publique o valor gerado da chave no GitHub.

### 1. Clonar o repositório

```bash
git clone https://github.com/GabrielaAmabily/agrogest.git
cd agrogest
```

### 2. Criar e ativar o ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
python -m pip install -r requirements.txt
```

Em sistemas que usam `python3` no lugar de `python`, substitua o comando pelo executável correspondente.

### 4. Configurar a chave secreta — obrigatório

**Windows (PowerShell):**

```powershell
$env:AGROGEST_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

**Linux/macOS:**

```bash
export AGROGEST_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

Esses comandos **geram uma chave nova**. Eles podem aparecer publicamente no README; o **valor gerado da chave**, não. A variável é válida apenas para a sessão atual do terminal; ao abrir um terminal novo, execute o comando novamente. Isso pode invalidar sessões de login anteriores, mas não remove os dados do SQLite.

### 5. Criar a conta do proprietário (primeira instalação)

```bash
python -m flask --app app criar-proprietario
```

Informe nome, e-mail e senha quando solicitado. O comando permite uma única conta de proprietário; em instalações existentes, não é necessário repeti-lo.

### 6. Iniciar o sistema

```bash
python app.py
```

Abra **http://127.0.0.1:5000** no navegador. O banco SQLite é criado automaticamente em `instance/agrogest.db` na primeira execução. Ele não é incluído no GitHub.

## Como testar os dois perfis

**Proprietário:** entre com o e-mail e a senha cadastrados no passo 5. Cadastre um fornecedor em **Fornecedores**, registre uma entrega e consulte **Pagamentos** e **Estoque**.

**Fornecedor:** abra o sistema em uma janela anônima ou saia da conta administrativa. Use **Cadastrar** para criar uma conta comum com outro e-mail. Depois entre novamente como proprietário, abra **Fornecedores → Vincular conta** e associe a conta recém-criada ao fornecedor comercial desejado. Saia e entre como fornecedor: no menu **Minhas entregas**, você verá somente o histórico correspondente àquele vínculo.

> A conta de fornecedor e o cadastro comercial são entidades separadas. Criar a conta no formulário público não vincula automaticamente um histórico comercial.

## Testes automatizados

```bash
python -m pip install -r requirements-test.txt
python -m pytest -v
```

Os testes automatizados utilizam uma aplicação Flask isolada e um banco de dados SQLite temporário, sem acessar o banco de desenvolvimento.

A suíte contém 8 testes automatizados, todos aprovados, abrangendo cálculos financeiros, bloqueio de edição após pagamento, entradas e saídas de estoque, saldo insuficiente, controle de validade, restrições de acesso e validação da categoria de defensivos.

Resultado da última execução: 8 testes aprovados em 3,57 segundos, utilizando Python 3.13.3 e pytest 9.2.0.

## Estrutura do projeto

```text
agrogest/
├── app.py                       # Aplicação Flask e rotas principais
├── models.py                    # Usuários, fornecedores e entregas
├── forms.py                     # Formulários
├── pagamentos.py                # Pagamentos e PDF
├── portal_fornecedor.py         # Vinculação e consulta individual
├── estoque.py                   # Insumos, lotes e movimentações
├── templates/                   # Páginas HTML e Jinja2
├── static/css/                  # Estilos
├── tests/                       # Testes automatizados
├── requirements.txt             # Dependências da aplicação
├── requirements-test.txt        # Dependências de teste
└── README.md
```

## Limitações e evoluções

O AgroGest é um MVP acadêmico. Entre os pontos para evoluir estão quantidades fracionárias no estoque, rastreabilidade de cada saída por lote, mais testes de concorrência e maior robustez para implantação em produção. A imutabilidade das entregas pagas é garantida pelo fluxo regular da aplicação, não por bloqueio imutável no banco de dados.

## Repositório e histórico

Código-fonte: https://github.com/GabrielaAmabily/agrogest

Histórico de desenvolvimento: https://github.com/GabrielaAmabily/agrogest/commits/main

## Autoria

**Gabriela Amabily Cézar** — Engenharia de Computação, UNIFEI.

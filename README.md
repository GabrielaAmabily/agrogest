# 🍓 AgroGest

**Sistema web de gestão de fornecedores, entregas, pagamentos e estoque de insumos para a produção de morangos.**

Projeto acadêmico desenvolvido na disciplina **Laboratório de Engenharia de Software I**, do curso de **Engenharia de Computação da Universidade Federal de Itajubá (UNIFEI)**.

## Sobre o projeto

O AgroGest foi criado para apoiar o controle de operações de um produtor de morangos. O sistema centraliza o cadastro de fornecedores, o registro de entregas e seus valores, o acompanhamento de pagamentos e a movimentação de materiais utilizados na produção.

A aplicação possui dois perfis de acesso:

- **Proprietário:** gerencia fornecedores, entregas, pagamentos e estoque de insumos.
- **Fornecedor:** consulta somente seu próprio histórico de entregas e os respectivos valores e pagamentos, quando sua conta está vinculada a um cadastro de fornecedor.

## Funcionalidades

### Fornecedores
- Cadastro, consulta e edição de fornecedores.
- Ativação e desativação de cadastros.
- Validação para evitar CPF/CNPJ duplicado.
- Vinculação de uma conta de usuário ao cadastro de fornecedor.

### Entregas e pagamentos
- Registro de entregas com data, fornecedor, quantidade de caixas e preço unitário.
- Cálculo automático do valor da entrega (**quantidade × preço unitário**).
- Filtros de consulta por fornecedor, período e situação de pagamento.
- Identificação de entregas pagas e não pagas.
- Confirmação de pagamentos e bloqueio da edição de entregas já pagas.
- Geração de relatório de pagamentos em PDF.

### Estoque de insumos
- Cadastro e edição de insumos, categoria, unidade de medida e estoque mínimo.
- Registro de entradas por lotes, com validade quando aplicável.
- Registro de saídas e atualização do saldo disponível.
- Bloqueio de saídas superiores ao estoque disponível e de consumo de lotes vencidos.
- Alertas de estoque baixo e de lotes vencidos ou próximos do vencimento.
- Consulta de lotes, descarte de lotes e histórico de movimentações.
- Desativação e reativação de insumos.

### Segurança
- Autenticação com senha armazenada por hash.
- Controle de acesso conforme o perfil do usuário.
- Restrição de dados do portal de fornecedores ao próprio fornecedor autenticado.
- Proteção CSRF nos formulários da aplicação.

## Tecnologias utilizadas

- **Python 3** e **Flask** — aplicação web.
- **Flask-SQLAlchemy** e **SQLite** — persistência de dados.
- **Flask-Login** — sessões e autenticação.
- **Flask-WTF** — formulários e proteção CSRF.
- **Bootstrap 5** — interface responsiva.
- **ReportLab** — geração de arquivos PDF.
- **pytest** — testes automatizados.
- **Git e GitHub** — versionamento do código.

## Como executar localmente

As instruções abaixo usam **PowerShell no Windows**. É necessário ter Python e Git instalados.

### 1. Clonar o repositório

```powershell
git clone https://github.com/GabrielaAmabily/agrogest.git
cd agrogest
```

### 2. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 4. Configurar a chave secreta

No PowerShell, configure uma chave para a sessão atual:

```powershell
$env:AGROGEST_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

> A chave é necessária para as sessões e os formulários. Ela não deve ser incluída no código-fonte nem enviada ao GitHub. O comando acima gera uma nova chave a cada sessão do terminal, o que pode invalidar logins anteriores.

### 5. Criar o usuário proprietário

Em uma instalação nova, execute:

```powershell
python -m flask --app app criar-proprietario
```

Informe nome, e-mail e senha quando solicitado. Esse comando é destinado à configuração inicial da aplicação; se já houver proprietário cadastrado, não é necessário repeti-lo.

### 6. Iniciar o servidor

```powershell
python app.py
```

Abra **http://127.0.0.1:5000** no navegador.

O SQLite é inicializado automaticamente na primeira execução. O arquivo local do banco não deve ser versionado.

## Como executar os testes

Instale as dependências de teste:

```powershell
python -m pip install -r requirements-test.txt
```

Execute:

```powershell
python -m pytest -v
```

Os testes usam uma aplicação Flask isolada e um banco SQLite temporário; não devem acessar o banco de desenvolvimento. Na última execução local registrada durante o desenvolvimento, **6 testes passaram**, contemplando cálculo financeiro, regras de estoque e restrições de acesso.

## Organização do projeto

```text
agrogest/
├── app.py                  # Configuração Flask e rotas principais
├── models.py               # Modelos centrais de dados
├── forms.py                # Formulários
├── pagamentos.py           # Consultas, confirmação de pagamentos e PDF
├── portal_fornecedor.py    # Vinculação e consulta individual
├── estoque.py              # Insumos, lotes e movimentações
├── templates/              # Páginas HTML / Jinja2
├── static/                 # Arquivos de estilo e recursos estáticos
├── tests/                  # Testes automatizados
├── requirements.txt        # Dependências da aplicação
├── requirements-test.txt   # Dependências adicionais de testes
└── README.md
```

## Regras de negócio de destaque

- O valor de cada entrega é calculado pela multiplicação da quantidade de caixas pelo preço unitário informado.
- Uma entrega marcada como paga não pode ser editada pelo fluxo normal do sistema.
- Cada fornecedor autenticado pode consultar somente os registros associados à sua conta vinculada.
- Saídas de estoque não podem exceder a quantidade disponível.
- Lotes vencidos não são considerados disponíveis para consumo.

## Limitações e evolução

O AgroGest é um **projeto acadêmico em desenvolvimento**. Entre os pontos de evolução estão:

- Suporte a quantidades fracionárias em algumas unidades de estoque.
- Rastreabilidade mais detalhada dos lotes utilizados em cada saída.
- Ampliação dos testes automatizados e testes de concorrência.
- Preparação e validação de uma implantação pública com configuração segura de produção.

## Autoria

**Gabriela Amabily Cézar**  
Engenharia de Computação — Universidade Federal de Itajubá (UNIFEI)

Repositório: https://github.com/GabrielaAmabily/agrogest

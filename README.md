# 🧁 Cupcake Store

Loja virtual de cupcakes desenvolvida para o **Projeto Integrador Transdisciplinar em Engenharia de Software II**, a partir do planejamento (PIT) de **Cassia Santi — RGM 28418549**.

Aplicação web completa com **área do cliente** (cadastro, login, vitrine com filtro por sabor, carrinho, checkout com Pix, acompanhamento e cancelamento de pedidos, painel e perfil) e **área administrativa** (dashboard, pedidos, usuários, produtos, estoque com entradas/saídas e configurações da loja).

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3.10+ · Flask 3 · padrão **MVC** |
| Banco de dados | **SQLite** (projeto físico em `app/models/schema.sql`) |
| Front-end | HTML5 (Jinja2) · CSS3 · JavaScript puro |
| Testes | **pytest** — 65 testes unitários e de integração |

---

## ▶️ Como executar

```bash
# 1. (opcional) ambiente virtual
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate

# 2. dependências
pip install -r requirements.txt

# 3. rodar
python run.py
```

Acesse **http://127.0.0.1:5000**. O banco é criado automaticamente na primeira execução (`instance/cupcake_store.sqlite`) com dados de demonstração.

Para recriar o banco do zero: `flask --app run init-db`

### Contas de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | admin@cupcakestore.com | Admin@123 |
| Cliente | cliente@email.com | Cliente@123 |

### Rodar os testes

```bash
python -m pytest -v
```

---

## 🗂️ Estrutura (MVC)

```
cupcake-store/
├── run.py                      # ponto de entrada
├── requirements.txt
├── app/
│   ├── __init__.py             # fábrica da aplicação, segurança (CSRF, headers), filtros
│   ├── models/                 # M — regras de negócio + acesso ao banco
│   │   ├── schema.sql          #     projeto físico do banco (DDL)
│   │   ├── database.py         #     conexão, utilitários, auditoria
│   │   ├── user.py             #     usuários e perfis (HU-001, 002, 009, 017)
│   │   ├── product.py          #     catálogo (HU-003, 013, 015, 016)
│   │   ├── cart.py             #     carrinho (HU-010, 011, 012)
│   │   ├── order.py            #     pedidos, Pix, cancelamento (HU-004..008, 014)
│   │   ├── stock.py            #     estoque (HU-019)
│   │   ├── store_config.py     #     configurações da loja (HU-018)
│   │   └── seed.py             #     dados de demonstração
│   ├── controllers/            # C — rotas (Flask Blueprints)
│   │   ├── auth.py  shop.py  cart.py  orders.py  profile.py  admin.py
│   │   └── helpers.py          #     login_required / admin_required
│   ├── templates/              # V — telas HTML (Jinja2), seguindo os mockups do PIT
│   └── static/                 #     CSS, JS, imagens
├── tests/                      # testes automatizados (pytest)
├── tools/gen_images.py         # gera as ilustrações SVG dos produtos
└── docs/                       # documentação por situação-problema
    ├── situacao-1/             # revisão do planejamento, modelo de dados, dicionário
    ├── situacao-2/             # arquitetura e manual de uso
    └── situacao-3/             # plano/relatório de testes e formulário para testadores
```

---

## ✅ Histórias de usuário implementadas

| ID | História | Onde |
|---|---|---|
| 001 | Criação de conta (e-mail único, senha forte) | `/registro` |
| 002 | Login com senha criptografada (hash) | `/login` |
| 003 | Painel do usuário + filtro por sabor na vitrine + layout responsivo | `/minha-conta`, `/` |
| 004 | Acompanhar status e detalhes do pedido (linha do tempo) | `/pedidos/<id>` |
| 005 | Histórico completo de compras | `/pedidos` |
| 006 | Finalização do pedido (entrega ou retirada, forma de pagamento) | `/checkout` |
| 007 | Confirmação da transação (Pix com QR Code / dinheiro) | `/pedidos/<id>` |
| 008 | Cancelamento dentro do prazo e antes do envio, com estorno de estoque | `/pedidos/<id>` |
| 009 | Atualização do perfil e da conta (e-mail/senha) | `/minha-conta/perfil`, `/minha-conta/conta` |
| 010–012 | Carrinho: revisar, adicionar (com confirmação visual), alterar e remover | `/carrinho` |
| 013 | Adicionar produtos com validação e imagem | `/admin/produtos/novo` |
| 014 | Lista de pedidos com filtros e ordenação | `/admin/pedidos` |
| 015 | Atualizar produto com registro das alterações (auditoria) | `/admin/produtos/<id>/editar` |
| 016 | Excluir produto (irreversível, confirmação digitando o nome) | `/admin/produtos` |
| 017 | Gerenciar usuários (ativar/desativar, admin, redefinir senha, auditoria) | `/admin/usuarios` |
| 018 | Configurações da loja (endereço, pagamento, entrega, prazo de cancelamento) | `/admin/configuracoes/...` |
| 019 | Estoque: entradas/saídas e histórico com cores | `/admin/estoque` |

> **Login social (HU-001 CA#4):** os botões Google/Telefone aparecem na tela de login como "versão futura", pois exigem credenciais OAuth de produção.
> **Pagamento Pix:** o código "copia e cola" segue o padrão BR Code (EMV + CRC16) e o QR Code é real, mas a confirmação bancária é **simulada** (botão "Já paguei") por se tratar de ambiente acadêmico.

---

## 🔒 Segurança (RNFs)

- Senhas com hash (Werkzeug PBKDF2/scrypt) — nunca armazenadas em texto.
- Proteção **CSRF** em todos os formulários, cookies `HttpOnly` / `SameSite=Lax`.
- Consultas SQL parametrizadas (sem concatenação de dados do usuário).
- Controle de acesso por perfil (cliente × administrador) e isolamento de pedidos por usuário.
- Trilha de auditoria (`audit_logs`) para ações administrativas.

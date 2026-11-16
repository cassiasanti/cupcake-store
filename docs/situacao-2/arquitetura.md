# Situação 2 — Arquitetura da solução

## Padrão MVC

```
Navegador ──HTTP──▶ Controller (Blueprint Flask)
                       │  valida sessão/permissão, lê o formulário
                       ▼
                    Model (app/models/*.py)
                       │  aplica as regras de negócio, SQL parametrizado
                       ▼
                    SQLite (instance/cupcake_store.sqlite)
                       │
Controller ◀───────────┘
   │  render_template(...)
   ▼
View (templates Jinja2 + CSS + JS) ──HTML──▶ Navegador
```

- **Model** — `app/models/`. Concentra todas as regras de negócio. Quando uma regra é violada, lança `ValidationError` com a mensagem que o usuário vai ver. Não depende de HTTP, e por isso pode ser testado isoladamente.
- **Controller** — `app/controllers/`. Um Blueprint por área: `auth`, `shop`, `cart`, `orders`, `profile` e `admin`. Recebe a requisição, chama o Model, trata o `ValidationError` com `flash()` e decide se renderiza uma tela ou redireciona.
- **View** — `app/templates/` e `app/static/`. Telas em HTML/Jinja2 que seguem os mockups. O JavaScript (sem frameworks) cuida dos toasts, do carrinho assíncrono, das máscaras, do medidor de senha e das confirmações.

## Transações importantes
- **Checkout (`order.checkout`)** — numa única transação: cria o pedido e os itens, baixa o estoque (movimentações de saída), grava o snapshot de entrega, registra o histórico de status e fecha o carrinho. Se algo falhar, tudo é desfeito (`rollback`).
- **Cancelamento (`order.cancel`)** — devolve o estoque (entradas de estorno) e marca o pedido como `cancelado`, também numa única transação.

## Máquina de estados do pedido

```
aguardando_pagamento ──▶ pago ──▶ em_preparo ──▶ enviado ──▶ entregue
        │                  │          │   └──────(retirada)──────▲
        └──────────────────┴──────────┴──▶ cancelado
```
- **Pedido em dinheiro:** começa em `em_preparo`.
- **Cancelamento pelo cliente:** só antes de `enviado` e dentro do prazo configurado.
- **Cancelamento pelo admin:** antes de `enviado`, sem prazo.

## Segurança
- **Senhas:** hash com Werkzeug.
- **Formulários:** token CSRF por sessão, validado em todo POST.
- **Cookies:** `HttpOnly` e `SameSite=Lax`.
- **Cabeçalhos HTTP:** `X-Frame-Options`, `X-Content-Type-Options` e `Referrer-Policy`.
- **Permissões:** decorators `login_required` e `admin_required`.
- **Isolamento:** consultas de pedido sempre filtradas pelo `profile_id` do usuário logado.
- **Uploads:** extensão validada, nome aleatório e limite de 3 MB.

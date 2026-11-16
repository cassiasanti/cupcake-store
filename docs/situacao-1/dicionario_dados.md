# Dicionário de Dados — Cupcake Store

SGBD: **SQLite 3** · DDL completo em [`schema.sql`](schema.sql).

## users

Credenciais de acesso e permissões.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| email | VARCHAR(100) | Não |  |  | E-mail (único, minúsculo) |
| password | VARCHAR(255) | Não |  |  | Hash da senha |
| is_active | NUMERIC | Não | 1 |  | 1 = ativo, 0 = inativo |
| is_staff | NUMERIC | Não | 0 |  | 1 = administrador |
| first_login | TIMESTAMP | Sim |  |  | Primeiro acesso |
| last_login | TIMESTAMP | Sim |  |  | Último acesso |

## profiles

Dados pessoais e de entrega do usuário (1:1 com users).

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| user_id | INTEGER | Não |  | FK → users.id | FK → users.id |
| first_name | VARCHAR(100) | Não |  |  | Nome |
| last_name | VARCHAR(100) | Não |  |  | Sobrenome |
| address | VARCHAR(200) | Sim |  |  | Logradouro, número e complemento |
| city | VARCHAR(100) | Sim |  |  | Cidade |
| state | VARCHAR(100) | Sim |  |  | UF |
| postal_code | VARCHAR(20) | Sim |  |  | CEP (00000-000) |
| phone_number | VARCHAR(20) | Sim |  |  | Telefone com DDD |

## products

Catálogo de cupcakes.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| name | TEXT | Não |  |  | Nome |
| description | TEXT | Não |  |  | Descrição |
| flavor | TEXT | Não | 'Outros' |  | Sabor (filtro da vitrine) |
| price | REAL | Não |  |  | Preço unitário em R$ (> 0) |
| ingredients | TEXT | Sim |  |  | Lista de ingredientes |
| image | TEXT | Sim |  |  | Caminho/URL da imagem |
| thumbnail | TEXT | Sim |  |  | Miniatura |
| current_stock | INTEGER | Não | 0 |  | Saldo atual em estoque (≥ 0) |
| is_active | NUMERIC | Não | 1 |  | 1 = ativo, 0 = inativo |

## stocks

Movimentações de estoque (entrada/saída).

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| profile_id | INTEGER | Sim |  | FK → profiles.id | FK → profiles.id |
| product_id | INTEGER | Não |  | FK → products.id | FK → products.id |
| quantity | INTEGER | Não |  |  | Quantidade (> 0) |
| type | TEXT | Não |  |  | 'entrada' ou 'saida' |
| note | TEXT | Sim |  |  | Observação |

## shopping_carts

Carrinho do cliente; vira histórico ao ser vinculado a um pedido.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| profile_id | INTEGER | Não |  | FK → profiles.id | FK → profiles.id |
| total | REAL | Não | 0 |  | Valor total em R$ |
| order_id | INTEGER | Sim |  | FK → orders.id | FK → orders.id |

## shopping_cart_items

Itens de um carrinho.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| shopping_cart_id | INTEGER | Não |  | FK → shopping_carts.id | FK → shopping_carts.id |
| product_id | INTEGER | Não |  | FK → products.id | FK → products.id |
| item_price | REAL | Não |  |  | Preço unitário aplicado |
| quantity | INTEGER | Não |  |  | Quantidade (> 0) |

## orders

Pedidos realizados.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| profile_id | INTEGER | Não |  | FK → profiles.id | FK → profiles.id |
| shopping_cart_id | INTEGER | Não |  | FK → shopping_carts.id | FK → shopping_carts.id |
| status | TEXT | Não | 'aguardando_pagamento' |  | Status do pedido |
| payment_method | TEXT | Não |  |  | 'pix' ou 'dinheiro' |
| pix_qr | TEXT | Sim |  |  | Conteúdo do QR Code Pix |
| pix_string | TEXT | Sim |  |  | Pix copia e cola (BR Code) |
| pix_transaction_id | TEXT | Sim |  |  | TXID da cobrança Pix |
| pix_url | TEXT | Sim |  |  | URL de pagamento (reservado) |
| is_delivery | NUMERIC | Não | 0 |  | 1 = entrega, 0 = retirada |
| delivery_price | REAL | Não | 0 |  | Taxa de entrega |
| total | REAL | Não |  |  | Valor total em R$ |

## order_items

Snapshot dos itens/preços no momento da compra.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| order_id | INTEGER | Não |  | FK → orders.id | FK → orders.id |
| product_id | INTEGER | Não |  | FK → products.id | FK → products.id |
| name | TEXT | Não |  |  | Nome |
| item_price | REAL | Não |  |  | Preço unitário aplicado |
| quantity | INTEGER | Não |  |  | Quantidade (> 0) |

## order_status_history

Linha do tempo de status de cada pedido.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| order_id | INTEGER | Não |  | FK → orders.id | FK → orders.id |
| status | TEXT | Não |  |  | Status do pedido |

## order_delivery_details

Snapshot dos endereços do cliente e da loja no momento do pedido.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| order_id | INTEGER | Não |  | FK → orders.id | FK → orders.id |
| user_first_name | VARCHAR(100) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_last_name | VARCHAR(100) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_email | VARCHAR(100) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_address | VARCHAR(200) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_city | VARCHAR(100) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_state | VARCHAR(100) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_postal_code | VARCHAR(20) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| user_phone_number | VARCHAR(20) | Sim |  |  | Cópia do dado do cliente no momento do pedido |
| store_email | VARCHAR(100) | Sim |  |  | Cópia do dado da loja no momento do pedido |
| store_address | VARCHAR(200) | Sim |  |  | Cópia do dado da loja no momento do pedido |
| store_city | VARCHAR(100) | Sim |  |  | Cópia do dado da loja no momento do pedido |
| store_state | VARCHAR(100) | Sim |  |  | Cópia do dado da loja no momento do pedido |
| store_postal_code | VARCHAR(20) | Sim |  |  | Cópia do dado da loja no momento do pedido |
| store_phone_number | VARCHAR(20) | Sim |  |  | Cópia do dado da loja no momento do pedido |

## store_configs

Configurações gerais da loja (registro único).

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| updated_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora da última alteração (UTC) |
| deleted_at | DATETIME | Sim |  |  | Exclusão lógica (NULL = ativo) |
| store_name | VARCHAR(100) | Não | 'Cupcake Store' |  | Nome da loja |
| delivery_price | REAL | Não | 0 |  | Taxa de entrega |
| delivery_is_active | NUMERIC | Não | 1 |  | Entrega habilitada |
| payment_cash_is_active | NUMERIC | Não | 1 |  | Aceita dinheiro |
| payment_pix_is_active | NUMERIC | Não | 1 |  | Aceita Pix |
| pix_key | TEXT | Sim |  |  | Chave Pix da loja |
| pix_key_type | TEXT | Sim |  |  | Tipo da chave (cpf, cnpj, email, telefone, aleatoria) |
| cancel_window_minutes | INTEGER | Não | 60 |  | Prazo (min) para o cliente cancelar; 0 = até o envio |
| physical_store_email | VARCHAR(100) | Sim |  |  | Dados da loja física: email |
| physical_store_address | VARCHAR(200) | Sim |  |  | Dados da loja física: address |
| physical_store_city | VARCHAR(100) | Sim |  |  | Dados da loja física: city |
| physical_store_state | VARCHAR(100) | Sim |  |  | Dados da loja física: state |
| physical_store_postal_code | VARCHAR(20) | Sim |  |  | Dados da loja física: postal_code |
| physical_store_phone_number | VARCHAR(20) | Sim |  |  | Dados da loja física: phone_number |
| opening_hours | VARCHAR(100) | Sim |  |  | Horário de funcionamento |

## audit_logs

Trilha de auditoria de ações administrativas.

| Coluna | Tipo | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| id | INTEGER | Não |  | PK | Identificador único (PK, autoincremento) |
| created_at | DATETIME | Não | CURRENT_TIMESTAMP |  | Data/hora de criação (UTC) |
| user_id | INTEGER | Sim |  | FK → users.id | FK → users.id |
| entity | TEXT | Não |  |  | Entidade afetada |
| entity_id | INTEGER | Sim |  |  | ID do registro afetado |
| action | TEXT | Não |  |  | Ação executada |
| details | TEXT | Sim |  |  | Detalhes da alteração |

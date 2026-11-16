-- =============================================================
-- Cupcake Store - Projeto físico do banco de dados (SQLite)
-- Baseado no Diagrama de Classes do PIT (Cassia Santi)
-- =============================================================
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  DATETIME,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,               -- hash (PBKDF2/scrypt)
    is_active   NUMERIC NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    is_staff    NUMERIC NOT NULL DEFAULT 0 CHECK (is_staff IN (0,1)),
    first_login TIMESTAMP,
    last_login  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at   DATETIME,
    user_id      INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    address      VARCHAR(200),
    city         VARCHAR(100),
    state        VARCHAR(100),
    postal_code  VARCHAR(20),
    phone_number VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at    DATETIME,
    name          TEXT NOT NULL,
    description   TEXT NOT NULL,
    flavor        TEXT NOT NULL DEFAULT 'Outros',     -- HU-003 CA#2: filtro por sabor
    price         REAL NOT NULL CHECK (price > 0),
    ingredients   TEXT,
    image         TEXT,
    thumbnail     TEXT,
    current_stock INTEGER NOT NULL DEFAULT 0 CHECK (current_stock >= 0),
    is_active     NUMERIC NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);

CREATE TABLE IF NOT EXISTS stocks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  DATETIME,
    profile_id  INTEGER REFERENCES profiles(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    type        TEXT NOT NULL CHECK (type IN ('entrada','saida')),
    note        TEXT
);

CREATE TABLE IF NOT EXISTS shopping_carts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  DATETIME,
    profile_id  INTEGER NOT NULL REFERENCES profiles(id),
    total       REAL NOT NULL DEFAULT 0,
    order_id    INTEGER REFERENCES orders(id)          -- preenchido ao finalizar
);

CREATE TABLE IF NOT EXISTS shopping_cart_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at       DATETIME,
    shopping_cart_id INTEGER NOT NULL REFERENCES shopping_carts(id) ON DELETE CASCADE,
    product_id       INTEGER NOT NULL REFERENCES products(id),
    item_price       REAL NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    UNIQUE (shopping_cart_id, product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at          DATETIME,
    profile_id          INTEGER NOT NULL REFERENCES profiles(id),
    shopping_cart_id    INTEGER NOT NULL REFERENCES shopping_carts(id),
    status              TEXT NOT NULL DEFAULT 'aguardando_pagamento'
                        CHECK (status IN ('aguardando_pagamento','pago','em_preparo',
                                          'enviado','entregue','cancelado')),
    payment_method      TEXT NOT NULL CHECK (payment_method IN ('pix','dinheiro')),
    pix_qr              TEXT,
    pix_string          TEXT,
    pix_transaction_id  TEXT,
    pix_url             TEXT,
    is_delivery         NUMERIC NOT NULL DEFAULT 0 CHECK (is_delivery IN (0,1)),
    delivery_price      REAL NOT NULL DEFAULT 0,
    total               REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    -- snapshot dos itens do pedido (preço no momento da compra)
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    name        TEXT NOT NULL,
    item_price  REAL NOT NULL,
    quantity    INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS order_status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_delivery_details (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at          DATETIME,
    order_id            INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    user_first_name     VARCHAR(100),
    user_last_name      VARCHAR(100),
    user_email          VARCHAR(100),
    user_address        VARCHAR(200),
    user_city           VARCHAR(100),
    user_state          VARCHAR(100),
    user_postal_code    VARCHAR(20),
    user_phone_number   VARCHAR(20),
    store_email         VARCHAR(100),
    store_address       VARCHAR(200),
    store_city          VARCHAR(100),
    store_state         VARCHAR(100),
    store_postal_code   VARCHAR(20),
    store_phone_number  VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS store_configs (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at                   DATETIME,
    store_name                   VARCHAR(100) NOT NULL DEFAULT 'Cupcake Store',
    delivery_price               REAL NOT NULL DEFAULT 0 CHECK (delivery_price >= 0),
    delivery_is_active           NUMERIC NOT NULL DEFAULT 1,
    payment_cash_is_active       NUMERIC NOT NULL DEFAULT 1,
    payment_pix_is_active        NUMERIC NOT NULL DEFAULT 1,
    pix_key                      TEXT,
    pix_key_type                 TEXT,
    cancel_window_minutes        INTEGER NOT NULL DEFAULT 60,   -- HU-008 CA#1 prazo
    physical_store_email         VARCHAR(100),
    physical_store_address       VARCHAR(200),
    physical_store_city          VARCHAR(100),
    physical_store_state         VARCHAR(100),
    physical_store_postal_code   VARCHAR(20),
    physical_store_phone_number  VARCHAR(20),
    opening_hours                VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    -- HU-015 RN#1 e HU-017 CA#3: rastreabilidade de ações administrativas
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id     INTEGER REFERENCES users(id),
    entity      TEXT NOT NULL,
    entity_id   INTEGER,
    action      TEXT NOT NULL,
    details     TEXT
);

CREATE INDEX IF NOT EXISTS ix_orders_profile ON orders(profile_id);
CREATE INDEX IF NOT EXISTS ix_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS ix_stocks_product ON stocks(product_id);
CREATE INDEX IF NOT EXISTS ix_products_flavor ON products(flavor);

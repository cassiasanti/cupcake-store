"""Dados iniciais para demonstração (executado somente com o banco vazio)."""
from .database import get_db, query

PRODUCTS = [
    ("Chocolate Intenso", "Massa de cacau 70% com cobertura de ganache cremosa e raspas de chocolate belga.",
     "Chocolate", 9.90, "Farinha, cacau 70%, ovos, açúcar, manteiga, creme de leite, chocolate belga", "chocolate.svg", 30),
    ("Brigadeiro Gourmet", "Cupcake de chocolate recheado de brigadeiro e finalizado com granulado belga.",
     "Chocolate", 10.90, "Farinha, cacau, leite condensado, manteiga, granulado belga", "brigadeiro.svg", 25),
    ("Baunilha Clássico", "Massa leve de baunilha de Madagascar com buttercream suíço e confeitos coloridos.",
     "Baunilha", 8.50, "Farinha, ovos, açúcar, manteiga, fava de baunilha, confeitos", "baunilha.svg", 40),
    ("Morango com Chantilly", "Massa branca com recheio de morango fresco e cobertura de chantilly batido na hora.",
     "Morango", 10.50, "Farinha, ovos, morango, chantilly, açúcar", "morango.svg", 20),
    ("Red Velvet", "O clássico americano: massa aveludada vermelha com frosting de cream cheese.",
     "Red Velvet", 11.90, "Farinha, cacau, leitelho, cream cheese, manteiga, açúcar", "redvelvet.svg", 18),
    ("Limão Siciliano", "Massa cítrica com raspas de limão siciliano, curd de limão e merengue maçaricado.",
     "Limão", 9.50, "Farinha, ovos, limão siciliano, açúcar, manteiga", "limao.svg", 15),
    ("Doce de Leite", "Massa amanteigada recheada com doce de leite argentino e cobertura de doce de leite.",
     "Doce de Leite", 10.00, "Farinha, ovos, doce de leite, manteiga, açúcar", "docedeleite.svg", 22),
    ("Baunilha & Frutas Vermelhas", "Baunilha com compota de frutas vermelhas e buttercream rosado.",
     "Baunilha", 10.90, "Farinha, ovos, baunilha, framboesa, mirtilo, manteiga", "frutasvermelhas.svg", 12),
    ("Unicórnio", "Massa de baunilha com buttercream em degradê turquesa e lilás e glitter comestível.",
     "Outros", 12.50, "Farinha, ovos, açúcar, manteiga, corante alimentício, glitter comestível", "unicornio.svg", 10),
    ("Café com Chocolate", "Massa de chocolate com toque de café espresso e cobertura de mousse de café.",
     "Chocolate", 10.50, "Farinha, cacau, café espresso, creme de leite, açúcar", "cafe.svg", 4),
]


def seed_data():
    if query("SELECT COUNT(*) c FROM users", one=True)["c"]:
        return
    from .user import create_user, update_profile

    admin_id = create_user("Cassia", "Santi", "admin@cupcakestore.com", "Admin@123", is_staff=True)
    update_profile(admin_id, {"first_name": "Cassia", "last_name": "Santi", "address": "Rua das Flores, 120",
                              "city": "São Paulo", "state": "SP", "postal_code": "01310-100",
                              "phone_number": "(11) 98888-7777"})
    client_id = create_user("Maria", "Oliveira", "cliente@email.com", "Cliente@123")
    update_profile(client_id, {"first_name": "Maria", "last_name": "Oliveira", "address": "Av. Paulista, 1000, ap 52",
                               "city": "São Paulo", "state": "SP", "postal_code": "01310-200",
                               "phone_number": "(11) 97777-6666"})
    db = get_db()
    db.execute(
        """INSERT INTO store_configs (store_name, delivery_price, delivery_is_active, payment_cash_is_active,
           payment_pix_is_active, pix_key, pix_key_type, cancel_window_minutes, physical_store_email,
           physical_store_address, physical_store_city, physical_store_state, physical_store_postal_code,
           physical_store_phone_number, opening_hours)
           VALUES ('Cupcake Store', 7.90, 1, 1, 1, 'contato@cupcakestore.com', 'email', 60,
           'contato@cupcakestore.com', 'Rua Augusta, 500', 'São Paulo', 'SP', '01305-000',
           '(11) 3333-4444', 'Seg a Sáb, 9h às 19h')"""
    )
    admin_profile = query("SELECT id FROM profiles WHERE user_id = ?", (admin_id,), one=True)["id"]
    for name, desc, flavor, price, ingr, img, stock in PRODUCTS:
        path = f"/static/img/products/{img}"
        cur = db.execute(
            """INSERT INTO products (name, description, flavor, price, ingredients, image, thumbnail, current_stock)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, desc, flavor, price, ingr, path, path, stock),
        )
        db.execute("INSERT INTO stocks (profile_id, product_id, quantity, type, note) VALUES (?,?,?,?,?)",
                   (admin_profile, cur.lastrowid, stock, "entrada", "Estoque inicial"))
    db.commit()

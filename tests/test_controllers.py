"""Testes de integração das rotas (Controllers + Views)."""
import re

from app.models.database import query

from .conftest import ADMIN, CLIENT, login


def test_public_pages(client):
    for url in ["/", "/?sabor=Chocolate", "/?q=morango", "/?page=2", "/produto/1", "/login", "/registro"]:
        assert client.get(url).status_code == 200, url
    assert client.get("/produto/9999").status_code == 404


def test_register_flow(client):
    r = client.post("/registro", data={"first_name": "Rita", "last_name": "Souza", "email": "rita@mail.com",
                                       "password": "Rita@2026", "confirm": "Rita@2026"}, follow_redirects=True)
    assert "Conta criada com sucesso" in r.get_data(as_text=True)
    r = client.post("/registro", data={"first_name": "R", "last_name": "S", "email": "rita@mail.com",
                                       "password": "Rita@2026", "confirm": "Rita@2026"}, follow_redirects=True)


def test_register_weak_password_shows_error(client):
    r = client.post("/registro", data={"first_name": "R", "last_name": "S", "email": "r@mail.com",
                                       "password": "123", "confirm": "123"})
    assert "A senha precisa ter" in r.get_data(as_text=True)


def test_login_logout(client):
    r = client.post("/login", data={"email": "cliente@email.com", "password": "x"})
    assert "E-mail ou senha inválidos" in r.get_data(as_text=True)
    r = login(client, CLIENT)
    assert "Olá, Maria" in r.get_data(as_text=True)
    client.post("/logout")
    assert client.get("/carrinho/").status_code == 302


def test_protected_routes_redirect_to_login(client):
    for url in ["/carrinho/", "/checkout", "/pedidos", "/minha-conta/", "/minha-conta/perfil"]:
        r = client.get(url)
        assert r.status_code == 302 and "/login" in r.headers["Location"], url


def test_client_cannot_access_admin(client_logged):
    assert client_logged.get("/admin/").status_code == 403
    assert client_logged.get("/admin/produtos").status_code == 403


def test_full_purchase_flow(client_logged):
    c = client_logged
    r = c.post("/carrinho/adicionar/1", data={"quantity": 2}, headers={"X-Requested-With": "fetch"})
    assert r.get_json()["ok"] and r.get_json()["count"] == 2
    assert "Chocolate Intenso" in c.get("/carrinho/").get_data(as_text=True)
    page = c.get("/checkout?delivery=1&payment=pix").get_data(as_text=True)
    assert "Formas de Pagamento" in page and "Valor da Compra" in page
    r = c.post("/checkout", data={"payment": "pix", "delivery": "1"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Pague com Pix" in html and "<svg" in html
    oid = int(re.search(r"Pedido #(\d+)", html).group(1))
    r = c.post(f"/pedidos/{oid}/pagar", follow_redirects=True)
    assert "Pagamento confirmado" in r.get_data(as_text=True)
    assert f"#{oid}" in c.get("/pedidos").get_data(as_text=True)
    assert c.get("/minha-conta/").status_code == 200
    r = c.post(f"/pedidos/{oid}/cancelar", follow_redirects=True)
    assert "reembolso" in r.get_data(as_text=True)


def test_cart_errors_are_friendly(client_logged):
    r = client_logged.post("/carrinho/adicionar/10", data={"quantity": 999}, headers={"X-Requested-With": "fetch"})
    assert r.status_code == 400 and "estoque" in r.get_json()["message"]
    r = client_logged.post("/carrinho/item/9999/remover", follow_redirects=True)
    assert "não encontrado" in r.get_data(as_text=True)


def test_user_cannot_see_others_order(client, app):
    login(client, CLIENT)
    client.post("/carrinho/adicionar/1", data={"quantity": 1})
    client.post("/checkout", data={"payment": "dinheiro", "delivery": "0"})
    client.post("/logout")
    client.post("/registro", data={"first_name": "Eve", "last_name": "X", "email": "eve@mail.com",
                                   "password": "Eve@12345", "confirm": "Eve@12345"})
    assert client.get("/pedidos/1").status_code == 404


def test_profile_update(client_logged):
    r = client_logged.post("/minha-conta/perfil", data={"first_name": "Maria", "last_name": "Silva",
                           "address": "Rua A, 1", "city": "SP", "state": "SP", "postal_code": "01000-000",
                           "phone_number": "(11) 90000-0000"}, follow_redirects=True)
    assert "Perfil atualizado" in r.get_data(as_text=True)


def test_admin_pages(admin_logged):
    for url in ["/admin/", "/admin/pedidos", "/admin/pedidos?status=pago&sort=maior_valor", "/admin/usuarios",
                "/admin/usuarios?status=admins", "/admin/usuarios/novo", "/admin/usuarios/2", "/admin/produtos",
                "/admin/produtos/novo", "/admin/produtos/1/editar", "/admin/estoque", "/admin/estoque?product_id=3",
                "/admin/estoque/movimentacoes", "/admin/estoque/movimentacoes?type=saida",
                "/admin/configuracoes/endereco", "/admin/configuracoes/pagamento", "/admin/configuracoes/entrega"]:
        assert admin_logged.get(url).status_code == 200, url
    assert admin_logged.get("/admin/configuracoes/xyz").status_code == 404


def test_admin_product_crud(admin_logged, app):
    c = admin_logged
    r = c.post("/admin/produtos/novo", data={"name": "Pistache", "description": "Cupcake de pistache.",
               "flavor": "Outros", "price": "13,00", "initial_stock": "7", "is_active": "1"}, follow_redirects=True)
    assert "Produto cadastrado" in r.get_data(as_text=True)
    with app.app_context():
        p = query("SELECT * FROM products WHERE name='Pistache'", one=True)
    assert p["current_stock"] == 7
    r = c.post(f"/admin/produtos/{p['id']}/editar", data={"name": "Pistache Premium", "description": "Cupcake de pistache.",
               "flavor": "Outros", "price": "14", "is_active": "1"}, follow_redirects=True)
    assert "Produto atualizado" in r.get_data(as_text=True)
    r = c.post(f"/admin/produtos/{p['id']}/excluir", data={"confirm_name": "errado"}, follow_redirects=True)
    assert "Confirmação incorreta" in r.get_data(as_text=True)
    r = c.post(f"/admin/produtos/{p['id']}/excluir", data={"confirm_name": "Pistache Premium"}, follow_redirects=True)
    assert "excluído" in r.get_data(as_text=True)
    assert c.get(f"/produto/{p['id']}").status_code == 404


def test_admin_stock_and_users(admin_logged, app):
    c = admin_logged
    r = c.post("/admin/estoque", data={"product_id": 1, "type": "entrada", "quantity": 10}, follow_redirects=True)
    assert "Movimentação registrada" in r.get_data(as_text=True)
    r = c.post("/admin/estoque", data={"product_id": 1, "type": "saida", "quantity": 99999}, follow_redirects=True)
    assert "insuficiente" in r.get_data(as_text=True)
    r = c.post("/admin/usuarios/novo", data={"first_name": "Func", "last_name": "Loja", "email": "func@loja.com",
               "password": "Func@1234", "confirm": "Func@1234", "is_staff": "1"}, follow_redirects=True)
    assert "Usuário criado" in r.get_data(as_text=True)
    with app.app_context():
        uid = query("SELECT id FROM users WHERE email='func@loja.com'", one=True)["id"]
    r = c.post(f"/admin/usuarios/{uid}", data={"action": "toggle_active"}, follow_redirects=True)
    assert "desativada" in r.get_data(as_text=True)
    with app.app_context():
        assert query("SELECT COUNT(*) c FROM audit_logs WHERE entity='user' AND entity_id=?", (uid,), one=True)["c"] >= 2


def test_admin_config(admin_logged):
    r = admin_logged.post("/admin/configuracoes/entrega", data={"delivery_is_active": "1", "delivery_price": "9,99",
                          "cancel_window_minutes": "45"}, follow_redirects=True)
    assert "Configurações salvas" in r.get_data(as_text=True) and "9,99" in r.get_data(as_text=True)


def test_admin_order_status(admin_logged, app):
    c = admin_logged
    c.post("/carrinho/adicionar/1", data={"quantity": 1})
    c.post("/checkout", data={"payment": "pix", "delivery": "1"})
    r = c.post("/admin/pedidos/1", data={"status": "entregue"}, follow_redirects=True)
    assert "Não é possível" in r.get_data(as_text=True)
    r = c.post("/admin/pedidos/1", data={"status": "pago"}, follow_redirects=True)
    assert "Status atualizado" in r.get_data(as_text=True)


def test_csrf_protection(tmp_path):
    from app import create_app
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "c.sqlite")})
    c = app.test_client()
    r = c.post("/login", data={"email": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 400


# ---------------------------------------------------------- Correções do teste interno (15/11/2026)
def test_checkout_without_address_defaults_to_pickup(client):
    client.post("/registro", data={"first_name": "Sem", "last_name": "End", "email": "sem@end.com",
                                   "password": "Sem@12345", "confirm": "Sem@12345"})
    client.post("/carrinho/adicionar/1", data={"quantity": 1})
    html = client.get("/checkout").get_data(as_text=True)
    assert 'value="0" data-autosubmit-get checked' in html  # retirada pré-selecionada
    html = client.get("/checkout?delivery=1").get_data(as_text=True)
    assert "cadastre seu endereço no Perfil" in html


def test_reset_password_field_is_hidden(admin_logged):
    html = admin_logged.get("/admin/usuarios/2").get_data(as_text=True)
    assert 'type="password" id="np"' in html


def test_product_form_shows_brazilian_price(admin_logged):
    html = admin_logged.get("/admin/produtos/1/editar").get_data(as_text=True)
    assert 'value="9,90"' in html


def test_sales_card_lists_same_orders_as_its_total(admin_logged):
    c = admin_logged
    c.post("/carrinho/adicionar/1", data={"quantity": 1})
    c.post("/checkout", data={"payment": "pix", "delivery": "0"})       # aguardando pagamento: fora das vendas
    c.post("/carrinho/adicionar/3", data={"quantity": 1})
    c.post("/checkout", data={"payment": "dinheiro", "delivery": "0"})  # em preparo: conta como venda
    assert "admin/pedidos?vendas=1" in c.get("/admin/").get_data(as_text=True)
    html = c.get("/admin/pedidos?vendas=1").get_data(as_text=True)
    assert "<b>#2</b>" in html and "<b>#1</b>" not in html

"""Testes unitários das regras de negócio (camada Model)."""
import pytest

from app.models import cart, order, product, stock, store_config, user
from app.models.database import ValidationError, execute, query


def client_user():
    return user.get_user(query("SELECT id FROM users WHERE email='cliente@email.com'", one=True)["id"])


def admin_id():
    return query("SELECT id FROM users WHERE is_staff=1", one=True)["id"]


# ---------------------------------------------------------- HU-001 / HU-002
class TestUser:
    def test_create_user_ok(self, app):
        with app.app_context():
            uid = user.create_user("Ana", "Lima", "ANA@Mail.com", "Senha@123", "Senha@123")
            u = user.get_user(uid)
            assert u["email"] == "ana@mail.com"  # normalizado
            assert u["first_name"] == "Ana" and not u["is_staff"]

    @pytest.mark.parametrize("pw", ["curta1!", "semnumero!A", "SEMMINUSC1!", "semmaiusc1!", "SemEspecial1"])
    def test_weak_password_rejected(self, app, pw):
        with app.app_context(), pytest.raises(ValidationError):
            user.create_user("Ana", "Lima", "ana@mail.com", pw, pw)

    def test_password_mismatch(self, app):
        with app.app_context(), pytest.raises(ValidationError, match="não conferem"):
            user.create_user("Ana", "Lima", "ana@mail.com", "Senha@123", "Senha@124")

    def test_email_unique_and_valid(self, app):
        with app.app_context():
            with pytest.raises(ValidationError, match="já está cadastrado"):
                user.create_user("X", "Y", "cliente@email.com", "Senha@123")
            with pytest.raises(ValidationError, match="e-mail válido"):
                user.create_user("X", "Y", "invalido@", "Senha@123")

    def test_password_is_hashed(self, app):
        with app.app_context():
            row = query("SELECT password FROM users WHERE email='cliente@email.com'", one=True)
            assert "Cliente@123" not in row["password"]

    def test_authenticate(self, app):
        with app.app_context():
            assert user.authenticate("cliente@email.com", "Cliente@123")
            with pytest.raises(ValidationError):
                user.authenticate("cliente@email.com", "errada")
            assert client_user()["last_login"] is not None

    def test_inactive_user_cannot_login(self, app):
        with app.app_context():
            u = client_user()
            user.set_active(u["id"], False, admin_id())
            with pytest.raises(ValidationError, match="desativada"):
                user.authenticate("cliente@email.com", "Cliente@123")

    def test_admin_cannot_deactivate_self(self, app):
        with app.app_context(), pytest.raises(ValidationError):
            user.set_active(admin_id(), False, admin_id())

    def test_update_profile_validation(self, app):
        with app.app_context():
            uid = client_user()["id"]
            with pytest.raises(ValidationError, match="CEP"):
                user.update_profile(uid, {"first_name": "M", "last_name": "O", "postal_code": "123"})
            user.update_profile(uid, {"first_name": "Mari", "last_name": "O", "postal_code": "01310-100",
                                      "phone_number": "(11) 91234-5678"})
            assert user.get_user(uid)["first_name"] == "Mari"

    def test_change_password(self, app):
        with app.app_context():
            uid = client_user()["id"]
            with pytest.raises(ValidationError, match="atual incorreta"):
                user.change_password(uid, "errada", "Nova@1234", "Nova@1234")
            user.change_password(uid, "Cliente@123", "Nova@1234", "Nova@1234")
            assert user.authenticate("cliente@email.com", "Nova@1234")


# ---------------------------------------------------------- HU-013/015/016
class TestProduct:
    data = {"name": "Pistache", "description": "Cupcake de pistache siciliano", "flavor": "Outros", "price": "12,90"}

    def test_create_and_catalog(self, app):
        with app.app_context():
            pid = product.create(self.data, admin_id())
            p = product.get(pid)
            assert p["price"] == 12.90
            names = [r["name"] for r in product.list_catalog(search="Pistache")["items"]]
            assert "Pistache" in names

    @pytest.mark.parametrize("field,value", [("name", "ab"), ("description", "curta"), ("price", "0"),
                                             ("price", "abc"), ("flavor", "Pizza")])
    def test_validation(self, app, field, value):
        with app.app_context(), pytest.raises(ValidationError):
            product.create({**self.data, field: value}, admin_id())

    def test_update_is_audited_and_updates_cart_price(self, app):
        with app.app_context():
            u = client_user()
            cart.add(u["profile_id"], 1, 2)
            changes = product.update(1, {**dict(product.get(1)), "price": "15.00"}, admin_id())
            assert any("price" in c for c in changes)
            assert product.history(1)[0]["action"] == "update"
            c = cart.open_cart(u["profile_id"])
            assert cart.items(c["id"])[0]["item_price"] == 15.0

    def test_delete_removes_from_catalog_and_carts(self, app):
        with app.app_context():
            u = client_user()
            cart.add(u["profile_id"], 2, 1)
            product.delete(2, admin_id())
            assert product.get(2) is None
            assert cart.count(u["profile_id"]) == 0
            assert all(r["id"] != 2 for r in product.list_catalog()["items"])

    def test_filter_by_flavor(self, app):
        with app.app_context():
            items = product.list_catalog(flavor="Chocolate")["items"]
            assert items and all(i["flavor"] == "Chocolate" for i in items)

    def test_pagination(self, app):
        with app.app_context():
            p1 = product.list_catalog(page=1)
            p2 = product.list_catalog(page=2)
            assert p1["pages"] == 2 and len(p1["items"]) == product.PER_PAGE
            assert len(p2["items"]) == p1["total"] - product.PER_PAGE


# ---------------------------------------------------------- HU-019
class TestStock:
    def test_entrada_e_saida(self, app):
        with app.app_context():
            before = product.get(1)["current_stock"]
            stock.move(1, "entrada", 5)
            stock.move(1, "saida", 3)
            assert product.get(1)["current_stock"] == before + 2
            types = [m["type"] for m in stock.movements(1)[:2]]
            assert types == ["saida", "entrada"]

    def test_saida_maior_que_estoque(self, app):
        with app.app_context(), pytest.raises(ValidationError, match="insuficiente"):
            stock.move(1, "saida", 10_000)

    @pytest.mark.parametrize("qty", [0, -1, "x"])
    def test_quantidade_invalida(self, app, qty):
        with app.app_context(), pytest.raises(ValidationError):
            stock.move(1, "entrada", qty)


# ---------------------------------------------------------- HU-010/011/012
class TestCart:
    def test_add_update_remove(self, app):
        with app.app_context():
            pid = client_user()["profile_id"]
            cart.add(pid, 1, 2)
            cart.add(pid, 1, 1)  # soma no mesmo item
            c = cart.open_cart(pid)
            items = cart.items(c["id"])
            assert len(items) == 1 and items[0]["quantity"] == 3
            cart.update_quantity(pid, items[0]["id"], 5)
            assert cart.recalc(c["id"]) == round(5 * items[0]["item_price"], 2)
            cart.remove(pid, items[0]["id"])
            assert cart.count(pid) == 0

    def test_cannot_exceed_stock(self, app):
        with app.app_context(), pytest.raises(ValidationError, match="estoque"):
            cart.add(client_user()["profile_id"], 10, 999)  # Café com Chocolate tem 4

    def test_inactive_product(self, app):
        with app.app_context():
            execute("UPDATE products SET is_active=0 WHERE id=3")
            with pytest.raises(ValidationError, match="indisponível"):
                cart.add(client_user()["profile_id"], 3, 1)


# ---------------------------------------------------------- HU-004..008
class TestOrder:
    def _checkout(self, payment="pix", delivery=True):
        u = client_user()
        cart.add(u["profile_id"], 1, 2)
        cart.add(u["profile_id"], 3, 1)
        return order.checkout(u, payment, delivery)

    def test_checkout_creates_order_and_lowers_stock(self, app):
        with app.app_context():
            s1, s3 = product.get(1)["current_stock"], product.get(3)["current_stock"]
            oid = self._checkout()
            o = order.get(oid)
            cfg = store_config.get()
            assert o["status"] == "aguardando_pagamento"
            assert o["total"] == round(2 * 9.90 + 8.50 + cfg["delivery_price"], 2)
            assert o["pix_string"].startswith("000201") and len(o["pix_string"]) > 50
            assert product.get(1)["current_stock"] == s1 - 2 and product.get(3)["current_stock"] == s3 - 1
            assert cart.count(client_user()["profile_id"]) == 0  # carrinho novo vazio
            assert o["user_address"] and o["store_address"]  # snapshot de entrega

    def test_pix_crc(self):
        s = order.build_pix_string("chave@pix.com", 10.0, "TX1")
        assert s[-4:] == order._crc16(s[:-4])

    def test_cash_goes_to_preparation(self, app):
        with app.app_context():
            oid = self._checkout("dinheiro", False)
            o = order.get(oid)
            assert o["status"] == "em_preparo" and o["delivery_price"] == 0

    def test_empty_cart(self, app):
        with app.app_context(), pytest.raises(ValidationError, match="vazio"):
            order.checkout(client_user(), "pix", False)

    def test_invalid_payment(self, app):
        with app.app_context():
            cart.add(client_user()["profile_id"], 1, 1)
            with pytest.raises(ValidationError, match="pagamento"):
                order.checkout(client_user(), "cartao", False)

    def test_disabled_payment_method(self, app):
        with app.app_context():
            execute("UPDATE store_configs SET payment_pix_is_active=0")
            cart.add(client_user()["profile_id"], 1, 1)
            with pytest.raises(ValidationError):
                order.checkout(client_user(), "pix", False)

    def test_delivery_requires_address(self, app):
        with app.app_context():
            uid = user.create_user("Sem", "End", "semend@mail.com", "Senha@123")
            u = user.get_user(uid)
            cart.add(u["profile_id"], 1, 1)
            with pytest.raises(ValidationError, match="endereço"):
                order.checkout(u, "pix", True)

    def test_confirm_pix(self, app):
        with app.app_context():
            oid = self._checkout()
            order.confirm_pix_payment(oid, client_user()["profile_id"])
            assert order.get(oid)["status"] == "pago"
            assert [h["status"] for h in order.status_history(oid)] == ["aguardando_pagamento", "pago"]

    def test_cancel_returns_stock(self, app):
        with app.app_context():
            before = product.get(1)["current_stock"]
            oid = self._checkout()
            order.confirm_pix_payment(oid, client_user()["profile_id"])
            refund = order.cancel(oid, client_user()["profile_id"])
            assert refund is True
            assert order.get(oid)["status"] == "cancelado"
            assert product.get(1)["current_stock"] == before

    def test_cannot_cancel_after_dispatch(self, app):
        with app.app_context():
            oid = self._checkout()
            a = admin_id()
            for st in ("pago", "em_preparo", "enviado"):
                order.admin_update_status(oid, st, a)
            with pytest.raises(ValidationError, match="despachado"):
                order.cancel(oid, client_user()["profile_id"])

    def test_cancel_window_expired(self, app):
        with app.app_context():
            oid = self._checkout()
            execute("UPDATE orders SET created_at = datetime('now','-2 hours') WHERE id=?", (oid,))
            with pytest.raises(ValidationError, match="prazo"):
                order.cancel(oid, client_user()["profile_id"])

    def test_invalid_status_transition(self, app):
        with app.app_context():
            oid = self._checkout()
            with pytest.raises(ValidationError):
                order.admin_update_status(oid, "entregue", admin_id())

    def test_other_user_cannot_see_order(self, app):
        with app.app_context():
            oid = self._checkout()
            assert order.get(oid, profile_id=999) is None


# ---------------------------------------------------------- HU-018
class TestStoreConfig:
    def test_payment_requires_one_method(self, app):
        with app.app_context(), pytest.raises(ValidationError, match="pelo menos"):
            store_config.update_payment({}, admin_id())

    def test_pix_requires_key(self, app):
        with app.app_context(), pytest.raises(ValidationError, match="chave"):
            store_config.update_payment({"payment_pix_is_active": "1", "pix_key": ""}, admin_id())

    def test_delivery_update(self, app):
        with app.app_context():
            store_config.update_delivery({"delivery_is_active": "1", "delivery_price": "5,50",
                                          "cancel_window_minutes": "30"}, admin_id())
            cfg = store_config.get()
            assert cfg["delivery_price"] == 5.5 and cfg["cancel_window_minutes"] == 30
            with pytest.raises(ValidationError):
                store_config.update_delivery({"delivery_price": "-1"}, admin_id())


def test_pix_payload_is_ascii():
    s = order.build_pix_string("chave@pix.com", 5.0, "TX", "CONFEITARIA SÃO JOÃO", "SÃO PAULO")
    assert s.isascii() and "SAO PAULO" in s

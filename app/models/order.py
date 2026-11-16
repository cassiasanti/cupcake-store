"""Model de Pedido (HU-004, 005, 006, 007, 008, 014)."""
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone

from . import cart as cart_model
from . import stock as stock_model
from . import store_config
from .database import ValidationError, get_db, now, query

STATUS_LABELS = {
    "aguardando_pagamento": "Aguardando pagamento",
    "pago": "Pago",
    "em_preparo": "Em preparo",
    "enviado": "Saiu para entrega",
    "entregue": "Entregue",
    "cancelado": "Cancelado",
}
FLOW = ["aguardando_pagamento", "pago", "em_preparo", "enviado", "entregue"]
# HU-008 RN#1: só cancela se ainda não foi despachado
CANCELLABLE = ("aguardando_pagamento", "pago", "em_preparo")
# Transições permitidas para o administrador (HU-007 RN#1)
TRANSITIONS = {
    "aguardando_pagamento": ["pago", "cancelado"],
    "pago": ["em_preparo", "cancelado"],
    "em_preparo": ["enviado", "entregue", "cancelado"],
    "enviado": ["entregue"],
    "entregue": [],
    "cancelado": [],
}


# ---------------------------------------------------------------- Pix (simulado)
def _emv(tag, value):
    return f"{tag}{len(value):02d}{value}"


def _crc16(payload):
    crc = 0xFFFF
    for ch in payload.encode("utf-8"):
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def build_pix_string(key, amount, txid, merchant="CUPCAKE STORE", city="SAO PAULO"):
    """Gera um BR Code Pix 'copia e cola' (padrão EMV). Pagamento é simulado no projeto."""
    def ascii_(t):
        return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()

    merchant, city = ascii_(merchant), ascii_(city)
    account = _emv("00", "br.gov.bcb.pix") + _emv("01", key)
    payload = (
        _emv("00", "01") + _emv("26", account) + _emv("52", "0000") + _emv("53", "986")
        + _emv("54", f"{amount:.2f}") + _emv("58", "BR") + _emv("59", merchant[:25])
        + _emv("60", city[:15]) + _emv("62", _emv("05", txid[:25])) + "6304"
    )
    return payload + _crc16(payload)


# ---------------------------------------------------------------- Checkout
def summary(profile_id, is_delivery):
    cfg = store_config.get()
    cart = cart_model.open_cart(profile_id)
    items = cart_model.items(cart["id"])
    subtotal = round(sum(i["subtotal"] for i in items), 2)
    delivery = cfg["delivery_price"] if (is_delivery and cfg["delivery_is_active"]) else 0
    return {"cart": cart, "items": items, "subtotal": subtotal, "delivery": delivery,
            "total": round(subtotal + delivery, 2), "config": cfg}


def checkout(user, payment_method, is_delivery):
    """HU-006/007: finaliza o pedido, baixa estoque e fecha o carrinho (transação única)."""
    cfg = store_config.get()
    if payment_method not in [m for m, _ in store_config.payment_methods()]:
        raise ValidationError("Selecione uma forma de pagamento válida.")
    is_delivery = bool(is_delivery)
    if is_delivery and not cfg["delivery_is_active"]:
        raise ValidationError("Entrega indisponível no momento. Escolha retirar na loja.")
    if is_delivery and not (user["address"] and user["city"] and user["postal_code"]):
        raise ValidationError("Complete seu endereço no Perfil para receber em casa.")

    s = summary(user["profile_id"], is_delivery)
    if not s["items"]:
        raise ValidationError("Seu carrinho está vazio.")
    for i in s["items"]:
        if not i["is_active"]:
            raise ValidationError(f"'{i['name']}' não está mais disponível. Remova-o do carrinho.")
        if i["quantity"] > i["current_stock"]:
            raise ValidationError(f"Estoque insuficiente de '{i['name']}' (disponível: {i['current_stock']}).")

    db = get_db()
    try:
        status = "aguardando_pagamento" if payment_method == "pix" else "em_preparo"
        cur = db.execute(
            """INSERT INTO orders (profile_id, shopping_cart_id, status, payment_method, is_delivery,
               delivery_price, total) VALUES (?,?,?,?,?,?,?)""",
            (user["profile_id"], s["cart"]["id"], status, payment_method, 1 if is_delivery else 0,
             s["delivery"], s["total"]),
        )
        order_id = cur.lastrowid
        if payment_method == "pix":
            txid = "CUP" + uuid.uuid4().hex[:20].upper()
            pix = build_pix_string(cfg["pix_key"], s["total"], txid,
                                   cfg["store_name"].upper(), (cfg["physical_store_city"] or "SAO PAULO").upper())
            db.execute("UPDATE orders SET pix_string=?, pix_transaction_id=?, pix_qr=? WHERE id=?",
                       (pix, txid, pix, order_id))
        for i in s["items"]:
            db.execute(
                "INSERT INTO order_items (order_id, product_id, name, item_price, quantity) VALUES (?,?,?,?,?)",
                (order_id, i["product_id"], i["name"], i["item_price"], i["quantity"]),
            )
            stock_model.move(i["product_id"], "saida", i["quantity"], user["profile_id"],
                             f"Venda - pedido #{order_id}", commit=False)
        db.execute(
            """INSERT INTO order_delivery_details (order_id, user_first_name, user_last_name, user_email,
               user_address, user_city, user_state, user_postal_code, user_phone_number, store_email,
               store_address, store_city, store_state, store_postal_code, store_phone_number)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (order_id, user["first_name"], user["last_name"], user["email"], user["address"], user["city"],
             user["state"], user["postal_code"], user["phone_number"], cfg["physical_store_email"],
             cfg["physical_store_address"], cfg["physical_store_city"], cfg["physical_store_state"],
             cfg["physical_store_postal_code"], cfg["physical_store_phone_number"]),
        )
        db.execute("INSERT INTO order_status_history (order_id, status) VALUES (?,?)", (order_id, status))
        db.execute("UPDATE shopping_carts SET order_id = ?, updated_at = ? WHERE id = ?",
                   (order_id, now(), s["cart"]["id"]))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return order_id


def _set_status(order_id, status, commit=True):
    db = get_db()
    db.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (status, now(), order_id))
    db.execute("INSERT INTO order_status_history (order_id, status) VALUES (?,?)", (order_id, status))
    if commit:
        db.commit()


def confirm_pix_payment(order_id, profile_id):
    """Simula o retorno do gateway Pix (HU-007 CA#2/CA#3)."""
    order = get(order_id, profile_id)
    if not order:
        raise ValidationError("Pedido não encontrado.")
    if order["payment_method"] != "pix" or order["status"] != "aguardando_pagamento":
        raise ValidationError("Este pedido não está aguardando pagamento Pix.")
    _set_status(order_id, "pago")


# ---------------------------------------------------------------- Consulta
def get(order_id, profile_id=None):
    sql = """SELECT o.*, d.user_first_name, d.user_last_name, d.user_email, d.user_address, d.user_city,
                    d.user_state, d.user_postal_code, d.user_phone_number, d.store_email, d.store_address,
                    d.store_city, d.store_state, d.store_postal_code, d.store_phone_number
             FROM orders o LEFT JOIN order_delivery_details d ON d.order_id = o.id WHERE o.id = ?"""
    params = [order_id]
    if profile_id is not None:
        sql += " AND o.profile_id = ?"
        params.append(profile_id)
    return query(sql, params, one=True)


def order_items(order_id):
    return query(
        """SELECT oi.*, (oi.item_price * oi.quantity) AS subtotal, p.image
           FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?""",
        (order_id,),
    )


def status_history(order_id):
    return query("SELECT * FROM order_status_history WHERE order_id = ? ORDER BY id", (order_id,))


def list_for_profile(profile_id, limit=None):
    sql = """SELECT o.*, (SELECT COALESCE(SUM(quantity),0) FROM order_items WHERE order_id = o.id) AS items_count
             FROM orders o WHERE o.profile_id = ? ORDER BY o.id DESC"""
    if limit:
        sql += f" LIMIT {int(limit)}"
    return query(sql, (profile_id,))


def list_all(status="", search="", sort="recentes", date_from="", date_to=""):
    sql = """SELECT o.*, p.first_name, p.last_name, u.email,
                    (SELECT GROUP_CONCAT(quantity || 'x ' || name, ', ') FROM order_items WHERE order_id = o.id) AS items_desc
             FROM orders o JOIN profiles p ON p.id = o.profile_id JOIN users u ON u.id = p.user_id WHERE 1=1"""
    params = []
    if status:
        sql += " AND o.status = ?"
        params.append(status)
    if search:
        sql += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR u.email LIKE ? OR CAST(o.id AS TEXT) = ?)"
        params += [f"%{search}%"] * 3 + [search.lstrip("#")]
    if date_from:
        sql += " AND date(o.created_at) >= date(?)"
        params.append(date_from)
    if date_to:
        sql += " AND date(o.created_at) <= date(?)"
        params.append(date_to)
    order = {"recentes": "o.id DESC", "antigos": "o.id ASC", "maior_valor": "o.total DESC",
             "menor_valor": "o.total ASC", "cliente": "p.first_name COLLATE NOCASE"}.get(sort, "o.id DESC")
    return query(sql + f" ORDER BY {order}", params)


def can_cancel(order):
    if order["status"] not in CANCELLABLE:
        return False
    window = store_config.get()["cancel_window_minutes"]
    if window == 0:
        return True
    created = datetime.strptime(order["created_at"], "%Y-%m-%d %H:%M:%S")
    # created_at do SQLite é UTC
    return datetime.now(timezone.utc).replace(tzinfo=None) - created <= timedelta(minutes=window)


def cancel(order_id, profile_id=None, by_admin=False):
    """HU-008: cancela, devolve o estoque e sinaliza reembolso quando já pago."""
    order = get(order_id, None if by_admin else profile_id)
    if not order:
        raise ValidationError("Pedido não encontrado.")
    if order["status"] not in CANCELLABLE:
        raise ValidationError("Este pedido já foi despachado e não pode mais ser cancelado.")
    if not by_admin and not can_cancel(order):
        raise ValidationError("O prazo para cancelamento deste pedido expirou.")
    db = get_db()
    try:
        for i in order_items(order_id):
            stock_model.move(i["product_id"], "entrada", i["quantity"], profile_id,
                             f"Estorno - cancelamento do pedido #{order_id}", commit=False)
        _set_status(order_id, "cancelado", commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return order["status"] == "pago"  # True => reembolso necessário


def admin_update_status(order_id, new_status, actor_id):
    order = get(order_id)
    if not order:
        raise ValidationError("Pedido não encontrado.")
    if new_status not in TRANSITIONS[order["status"]]:
        raise ValidationError(
            f"Não é possível mudar de '{STATUS_LABELS[order['status']]}' para '{STATUS_LABELS.get(new_status, new_status)}'."
        )
    if new_status == "enviado" and not order["is_delivery"]:
        raise ValidationError("Pedido para retirada na loja: use 'Entregue' quando o cliente retirar.")
    if new_status == "cancelado":
        return cancel(order_id, actor_id, by_admin=True)
    _set_status(order_id, new_status)
    from .database import audit
    audit(actor_id, "order", order_id, "status", new_status)


def stats():
    r = query(
        """SELECT COUNT(*) AS orders,
                  COALESCE(SUM(CASE WHEN status NOT IN ('cancelado','aguardando_pagamento') THEN total END),0) AS sales,
                  COALESCE(SUM(CASE WHEN status IN ('aguardando_pagamento','pago','em_preparo','enviado') THEN 1 END),0) AS open_orders
           FROM orders""",
        one=True,
    )
    return dict(r)


def sales_last_days(days=7):
    return query(
        """SELECT date(created_at) d, COUNT(*) n, COALESCE(SUM(total),0) t FROM orders
           WHERE status NOT IN ('cancelado','aguardando_pagamento') AND date(created_at) >= date('now', ?)
           GROUP BY date(created_at) ORDER BY d""",
        (f"-{days - 1} day",),
    )

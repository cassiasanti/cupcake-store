"""Model de Carrinho de Compras (HU-010, 011, 012)."""
from .database import ValidationError, execute, get_db, now, query


def open_cart(profile_id):
    cart = query(
        "SELECT * FROM shopping_carts WHERE profile_id = ? AND order_id IS NULL AND deleted_at IS NULL",
        (profile_id,),
        one=True,
    )
    if cart:
        return cart
    cid = execute("INSERT INTO shopping_carts (profile_id, total) VALUES (?, 0)", (profile_id,))
    return query("SELECT * FROM shopping_carts WHERE id = ?", (cid,), one=True)


def items(cart_id):
    return query(
        """SELECT i.*, p.name, p.image, p.flavor, p.current_stock, p.is_active,
                  (i.item_price * i.quantity) AS subtotal
           FROM shopping_cart_items i JOIN products p ON p.id = i.product_id
           WHERE i.shopping_cart_id = ? AND p.deleted_at IS NULL ORDER BY i.id""",
        (cart_id,),
    )


def recalc(cart_id):
    total = query(
        "SELECT COALESCE(SUM(item_price * quantity), 0) t FROM shopping_cart_items WHERE shopping_cart_id = ?",
        (cart_id,),
        one=True,
    )["t"]
    execute("UPDATE shopping_carts SET total = ?, updated_at = ? WHERE id = ?", (round(total, 2), now(), cart_id))
    return round(total, 2)


def _product_for_cart(product_id):
    p = query(
        "SELECT * FROM products WHERE id = ? AND deleted_at IS NULL AND is_active = 1", (product_id,), one=True
    )
    if not p:
        raise ValidationError("Produto indisponível.")
    return p


def _parse_qty(quantity):
    try:
        q = int(quantity)
    except (TypeError, ValueError):
        raise ValidationError("Quantidade inválida.")
    if q <= 0:
        raise ValidationError("A quantidade deve ser maior que zero.")
    return q


def add(profile_id, product_id, quantity=1):
    qty = _parse_qty(quantity)
    product = _product_for_cart(product_id)
    cart = open_cart(profile_id)
    existing = query(
        "SELECT * FROM shopping_cart_items WHERE shopping_cart_id = ? AND product_id = ?",
        (cart["id"], product_id),
        one=True,
    )
    new_qty = qty + (existing["quantity"] if existing else 0)
    if new_qty > product["current_stock"]:
        raise ValidationError(
            f"Só temos {product['current_stock']} unidade(s) de '{product['name']}' em estoque."
        )
    if existing:
        execute("UPDATE shopping_cart_items SET quantity = ?, item_price = ?, updated_at = ? WHERE id = ?",
                (new_qty, product["price"], now(), existing["id"]))
    else:
        execute(
            "INSERT INTO shopping_cart_items (shopping_cart_id, product_id, item_price, quantity) VALUES (?,?,?,?)",
            (cart["id"], product_id, product["price"], qty),
        )
    recalc(cart["id"])
    return product


def update_quantity(profile_id, item_id, quantity):
    qty = _parse_qty(quantity)
    cart = open_cart(profile_id)
    item = query(
        "SELECT * FROM shopping_cart_items WHERE id = ? AND shopping_cart_id = ?", (item_id, cart["id"]), one=True
    )
    if not item:
        raise ValidationError("Item não encontrado no carrinho.")
    product = _product_for_cart(item["product_id"])
    if qty > product["current_stock"]:
        raise ValidationError(f"Só temos {product['current_stock']} unidade(s) de '{product['name']}'.")
    execute("UPDATE shopping_cart_items SET quantity = ?, updated_at = ? WHERE id = ?", (qty, now(), item_id))
    recalc(cart["id"])


def remove(profile_id, item_id):
    cart = open_cart(profile_id)
    item = query(
        """SELECT i.id, p.name FROM shopping_cart_items i JOIN products p ON p.id = i.product_id
           WHERE i.id = ? AND i.shopping_cart_id = ?""",
        (item_id, cart["id"]),
        one=True,
    )
    if not item:
        raise ValidationError("Item não encontrado no carrinho.")
    execute("DELETE FROM shopping_cart_items WHERE id = ?", (item_id,))
    recalc(cart["id"])
    return item["name"]


def count(profile_id):
    cart = query(
        "SELECT id FROM shopping_carts WHERE profile_id = ? AND order_id IS NULL", (profile_id,), one=True
    )
    if not cart:
        return 0
    return query(
        "SELECT COALESCE(SUM(quantity),0) c FROM shopping_cart_items WHERE shopping_cart_id = ?",
        (cart["id"],),
        one=True,
    )["c"]


def clear(profile_id):
    cart = open_cart(profile_id)
    get_db().execute("DELETE FROM shopping_cart_items WHERE shopping_cart_id = ?", (cart["id"],))
    get_db().commit()
    recalc(cart["id"])

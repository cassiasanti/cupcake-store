"""Model de Estoque (HU-019): entradas, saídas e histórico de movimentações."""
from .database import ValidationError, get_db, now, query


def move(product_id, mov_type, quantity, profile_id=None, note="", commit=True):
    """Registra uma movimentação e atualiza products.current_stock de forma atômica."""
    if mov_type not in ("entrada", "saida"):
        raise ValidationError("Tipo de movimentação inválido.")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValidationError("Quantidade inválida.")
    if quantity <= 0:
        raise ValidationError("A quantidade deve ser maior que zero.")
    db = get_db()
    product = db.execute(
        "SELECT id, name, current_stock FROM products WHERE id = ? AND deleted_at IS NULL", (product_id,)
    ).fetchone()
    if not product:
        raise ValidationError("Produto não encontrado.")
    delta = quantity if mov_type == "entrada" else -quantity
    if product["current_stock"] + delta < 0:
        raise ValidationError(
            f"Estoque insuficiente de '{product['name']}' (disponível: {product['current_stock']})."
        )
    db.execute(
        "INSERT INTO stocks (profile_id, product_id, quantity, type, note) VALUES (?,?,?,?,?)",
        (profile_id, product_id, quantity, mov_type, note),
    )
    db.execute(
        "UPDATE products SET current_stock = current_stock + ?, updated_at = ? WHERE id = ?",
        (delta, now(), product_id),
    )
    if commit:
        db.commit()
    return product["current_stock"] + delta


def movements(product_id=None, mov_type=""):
    sql = """SELECT s.*, p.name AS product_name, pr.first_name AS by_name
             FROM stocks s JOIN products p ON p.id = s.product_id
             LEFT JOIN profiles pr ON pr.id = s.profile_id WHERE 1=1"""
    params = []
    if product_id:
        sql += " AND s.product_id = ?"
        params.append(product_id)
    if mov_type in ("entrada", "saida"):
        sql += " AND s.type = ?"
        params.append(mov_type)
    return query(sql + " ORDER BY s.id DESC LIMIT 300", params)


def low_stock(limit=5):
    return query(
        "SELECT * FROM products WHERE deleted_at IS NULL AND current_stock <= ? ORDER BY current_stock",
        (limit,),
    )

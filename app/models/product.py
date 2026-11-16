"""Model de Produto / Catálogo (HU-003 CA#2, 013, 015, 016)."""
import math

from .database import ValidationError, audit, execute, get_db, now, query

FLAVORS = ["Chocolate", "Baunilha", "Morango", "Red Velvet", "Limão", "Doce de Leite", "Outros"]
EDITABLE = ("name", "description", "flavor", "price", "ingredients", "image", "is_active")
PER_PAGE = 8


def validate(data):
    """HU-013 RN#1: validação antes de publicar."""
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if len(name) < 3:
        raise ValidationError("O nome do produto deve ter pelo menos 3 caracteres.")
    if len(description) < 10:
        raise ValidationError("A descrição deve ter pelo menos 10 caracteres.")
    try:
        price = round(float(str(data.get("price", "")).replace(",", ".")), 2)
    except ValueError:
        raise ValidationError("Preço inválido.")
    if price <= 0:
        raise ValidationError("O preço deve ser maior que zero.")
    flavor = data.get("flavor") or "Outros"
    if flavor not in FLAVORS:
        raise ValidationError("Sabor inválido.")
    return {
        "name": name,
        "description": description,
        "flavor": flavor,
        "price": price,
        "ingredients": (data.get("ingredients") or "").strip(),
        "image": (data.get("image") or "").strip() or None,
        "is_active": 1 if str(data.get("is_active", "1")) in ("1", "on", "true", "True") else 0,
    }


def list_catalog(flavor="", search="", page=1):
    """Vitrine pública: somente produtos ativos e não excluídos."""
    where = "deleted_at IS NULL AND is_active = 1"
    params = []
    if flavor:
        where += " AND flavor = ?"
        params.append(flavor)
    if search:
        where += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{search}%"] * 2
    total = query(f"SELECT COUNT(*) c FROM products WHERE {where}", params, one=True)["c"]
    pages = max(1, math.ceil(total / PER_PAGE))
    page = min(max(1, page), pages)
    rows = query(
        f"SELECT * FROM products WHERE {where} ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?",
        (*params, PER_PAGE, (page - 1) * PER_PAGE),
    )
    return {"items": rows, "total": total, "page": page, "pages": pages}


def available_flavors():
    rows = query("SELECT DISTINCT flavor FROM products WHERE deleted_at IS NULL AND is_active = 1")
    present = {r["flavor"] for r in rows}
    return [f for f in FLAVORS if f in present]


def get(product_id, include_inactive=False):
    sql = "SELECT * FROM products WHERE id = ? AND deleted_at IS NULL"
    if not include_inactive:
        sql += " AND is_active = 1"
    return query(sql, (product_id,), one=True)


def list_admin(search="", sort="nome"):
    sql = "SELECT * FROM products WHERE deleted_at IS NULL"
    params = []
    if search:
        sql += " AND (name LIKE ? OR flavor LIKE ?)"
        params += [f"%{search}%"] * 2
    order = {"nome": "name COLLATE NOCASE", "preco": "price", "estoque": "current_stock",
             "recentes": "id DESC"}.get(sort, "name")
    return query(sql + f" ORDER BY {order}", params)


def create(data, actor_id):
    v = validate(data)
    pid = execute(
        """INSERT INTO products (name, description, flavor, price, ingredients, image, thumbnail, is_active)
           VALUES (?,?,?,?,?,?,?,?)""",
        (v["name"], v["description"], v["flavor"], v["price"], v["ingredients"], v["image"], v["image"], v["is_active"]),
    )
    audit(actor_id, "product", pid, "create", v["name"])
    return pid


def update(product_id, data, actor_id):
    """HU-015: atualização refletida imediatamente + registro de rastreabilidade."""
    current = get(product_id, include_inactive=True)
    if not current:
        raise ValidationError("Produto não encontrado.")
    if not data.get("image"):
        data = {**data, "image": current["image"]}
    v = validate(data)
    changes = [f"{k}: {current[k]!r} -> {v[k]!r}" for k in EDITABLE if str(current[k]) != str(v[k])]
    execute(
        """UPDATE products SET name=?, description=?, flavor=?, price=?, ingredients=?, image=?,
           thumbnail=?, is_active=?, updated_at=? WHERE id=?""",
        (v["name"], v["description"], v["flavor"], v["price"], v["ingredients"], v["image"], v["image"],
         v["is_active"], now(), product_id),
    )
    # Mantém o carrinho coerente com o preço mais recente (HU-010 RN#1)
    execute(
        """UPDATE shopping_cart_items SET item_price = ? WHERE product_id = ? AND shopping_cart_id IN
           (SELECT id FROM shopping_carts WHERE order_id IS NULL)""",
        (v["price"], product_id),
    )
    if changes:
        audit(actor_id, "product", product_id, "update", "; ".join(changes))
    return changes


def delete(product_id, actor_id):
    """HU-016: exclusão irreversível — some do catálogo e dos carrinhos abertos."""
    current = get(product_id, include_inactive=True)
    if not current:
        raise ValidationError("Produto não encontrado.")
    db = get_db()
    db.execute("UPDATE products SET deleted_at = ?, is_active = 0 WHERE id = ?", (now(), product_id))
    db.execute(
        """DELETE FROM shopping_cart_items WHERE product_id = ? AND shopping_cart_id IN
           (SELECT id FROM shopping_carts WHERE order_id IS NULL)""",
        (product_id,),
    )
    db.commit()
    audit(actor_id, "product", product_id, "delete", current["name"])


def count_products():
    return query("SELECT COUNT(*) c FROM products WHERE deleted_at IS NULL", one=True)["c"]


def history(product_id):
    return query(
        """SELECT a.*, p.first_name FROM audit_logs a LEFT JOIN profiles p ON p.user_id = a.user_id
           WHERE entity = 'product' AND entity_id = ? ORDER BY a.id DESC""",
        (product_id,),
    )

"""Model de Configuração da Loja (HU-018)."""
import re

from .database import ValidationError, audit, execute, now, query

ADDRESS_FIELDS = ("store_name", "physical_store_email", "physical_store_address", "physical_store_city",
                  "physical_store_state", "physical_store_postal_code", "physical_store_phone_number",
                  "opening_hours")
PIX_KEY_TYPES = ("cpf", "cnpj", "email", "telefone", "aleatoria")


def get():
    cfg = query("SELECT * FROM store_configs ORDER BY id LIMIT 1", one=True)
    if not cfg:
        execute("INSERT INTO store_configs (store_name) VALUES ('Cupcake Store')")
        cfg = query("SELECT * FROM store_configs ORDER BY id LIMIT 1", one=True)
    return cfg


def payment_methods():
    cfg = get()
    methods = []
    if cfg["payment_pix_is_active"] and cfg["pix_key"]:
        methods.append(("pix", "Pix"))
    if cfg["payment_cash_is_active"]:
        methods.append(("dinheiro", "Dinheiro (na entrega/retirada)"))
    return methods


def _update(fields, actor_id, section):
    cfg = get()
    sets = ", ".join(f"{k} = ?" for k in fields)
    execute(f"UPDATE store_configs SET {sets}, updated_at = ? WHERE id = ?", (*fields.values(), now(), cfg["id"]))
    audit(actor_id, "store_config", cfg["id"], f"update_{section}", str(fields))


def update_address(data, actor_id):
    fields = {k: (data.get(k) or "").strip() for k in ADDRESS_FIELDS}
    if not fields["store_name"]:
        raise ValidationError("O nome da loja é obrigatório.")
    if fields["physical_store_email"] and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", fields["physical_store_email"]):
        raise ValidationError("E-mail da loja inválido.")
    if fields["physical_store_postal_code"] and not re.match(r"^\d{5}-?\d{3}$", fields["physical_store_postal_code"]):
        raise ValidationError("CEP inválido.")
    _update(fields, actor_id, "address")


def update_payment(data, actor_id):
    pix = 1 if data.get("payment_pix_is_active") else 0
    cash = 1 if data.get("payment_cash_is_active") else 0
    key = (data.get("pix_key") or "").strip()
    key_type = data.get("pix_key_type") or ""
    if not pix and not cash:
        raise ValidationError("Mantenha pelo menos uma forma de pagamento ativa.")
    if pix and not key:
        raise ValidationError("Informe a chave Pix para ativar o pagamento via Pix.")
    if key and key_type not in PIX_KEY_TYPES:
        raise ValidationError("Selecione o tipo da chave Pix.")
    _update({"payment_pix_is_active": pix, "payment_cash_is_active": cash, "pix_key": key,
             "pix_key_type": key_type}, actor_id, "payment")


def update_delivery(data, actor_id):
    active = 1 if data.get("delivery_is_active") else 0
    try:
        price = round(float(str(data.get("delivery_price") or 0).replace(",", ".")), 2)
        window = int(data.get("cancel_window_minutes") or 60)
    except ValueError:
        raise ValidationError("Valores numéricos inválidos.")
    if price < 0:
        raise ValidationError("A taxa de entrega não pode ser negativa.")
    if window < 0:
        raise ValidationError("O prazo de cancelamento não pode ser negativo.")
    _update({"delivery_is_active": active, "delivery_price": price, "cancel_window_minutes": window},
            actor_id, "delivery")

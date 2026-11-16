"""Model de Usuário e Perfil (HU-001, 002, 009, 017)."""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from .database import ValidationError, audit, execute, get_db, now, query

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PROFILE_FIELDS = ("first_name", "last_name", "address", "city", "state", "postal_code", "phone_number")


def validate_email(email):
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("Informe um e-mail válido.")
    return email


def validate_password(password, confirm=None):
    """HU-001 RN#2: senha forte."""
    if confirm is not None and password != confirm:
        raise ValidationError("As senhas não conferem.")
    problems = []
    if len(password or "") < 8:
        problems.append("mínimo de 8 caracteres")
    if not re.search(r"[A-Z]", password or ""):
        problems.append("uma letra maiúscula")
    if not re.search(r"[a-z]", password or ""):
        problems.append("uma letra minúscula")
    if not re.search(r"\d", password or ""):
        problems.append("um número")
    if not re.search(r"[^A-Za-z0-9]", password or ""):
        problems.append("um caractere especial")
    if problems:
        raise ValidationError("A senha precisa ter: " + ", ".join(problems) + ".")


def email_exists(email, exclude_user_id=None):
    row = query("SELECT id FROM users WHERE email = ? AND deleted_at IS NULL", (email,), one=True)
    return row is not None and row["id"] != exclude_user_id


def create_user(first_name, last_name, email, password, confirm=None, is_staff=False, actor_id=None):
    first_name, last_name = (first_name or "").strip(), (last_name or "").strip()
    if not first_name or not last_name:
        raise ValidationError("Nome e sobrenome são obrigatórios.")
    email = validate_email(email)
    if email_exists(email):  # HU-001 RN#1
        raise ValidationError("Este e-mail já está cadastrado.")
    validate_password(password, confirm)
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (email, password, is_staff) VALUES (?,?,?)",
        (email, generate_password_hash(password), 1 if is_staff else 0),
    )
    user_id = cur.lastrowid
    db.execute(
        "INSERT INTO profiles (user_id, first_name, last_name) VALUES (?,?,?)",
        (user_id, first_name, last_name),
    )
    db.commit()
    if actor_id:
        audit(actor_id, "user", user_id, "create", email)
    return user_id


def authenticate(email, password):
    email = (email or "").strip().lower()
    user = query("SELECT * FROM users WHERE email = ? AND deleted_at IS NULL", (email,), one=True)
    if not user or not check_password_hash(user["password"], password or ""):
        raise ValidationError("E-mail ou senha inválidos.")
    if not user["is_active"]:
        raise ValidationError("Conta desativada. Entre em contato com a loja.")
    ts = now()
    execute(
        "UPDATE users SET last_login = ?, first_login = COALESCE(first_login, ?) WHERE id = ?",
        (ts, ts, user["id"]),
    )
    return user["id"]


def get_user(user_id):
    return query(
        """SELECT u.id, u.email, u.is_active, u.is_staff, u.created_at, u.last_login,
                  p.id AS profile_id, p.first_name, p.last_name, p.address, p.city,
                  p.state, p.postal_code, p.phone_number
           FROM users u JOIN profiles p ON p.user_id = u.id
           WHERE u.id = ? AND u.deleted_at IS NULL""",
        (user_id,),
        one=True,
    )


def update_profile(user_id, data, actor_id=None):
    """HU-009: atualização imediata do perfil."""
    values = {f: (data.get(f) or "").strip() for f in PROFILE_FIELDS}
    if not values["first_name"] or not values["last_name"]:
        raise ValidationError("Nome e sobrenome são obrigatórios.")
    if values["postal_code"] and not re.match(r"^\d{5}-?\d{3}$", values["postal_code"]):
        raise ValidationError("CEP inválido. Use o formato 00000-000.")
    if values["phone_number"] and len(re.sub(r"\D", "", values["phone_number"])) < 10:
        raise ValidationError("Telefone inválido. Informe DDD + número.")
    sets = ", ".join(f"{f} = ?" for f in PROFILE_FIELDS)
    execute(
        f"UPDATE profiles SET {sets}, updated_at = ? WHERE user_id = ?",
        (*values.values(), now(), user_id),
    )
    if actor_id and actor_id != user_id:
        audit(actor_id, "user", user_id, "update_profile", values["first_name"])


def update_email(user_id, email, actor_id=None):
    email = validate_email(email)
    if email_exists(email, exclude_user_id=user_id):
        raise ValidationError("Este e-mail já está cadastrado.")
    execute("UPDATE users SET email = ?, updated_at = ? WHERE id = ?", (email, now(), user_id))
    if actor_id and actor_id != user_id:
        audit(actor_id, "user", user_id, "update_email", email)


def change_password(user_id, current, new, confirm):
    user = query("SELECT password FROM users WHERE id = ?", (user_id,), one=True)
    if not check_password_hash(user["password"], current or ""):
        raise ValidationError("Senha atual incorreta.")
    validate_password(new, confirm)
    execute("UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
            (generate_password_hash(new), now(), user_id))


def admin_reset_password(user_id, new, actor_id):
    validate_password(new)
    execute("UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
            (generate_password_hash(new), now(), user_id))
    audit(actor_id, "user", user_id, "reset_password")


def set_active(user_id, active, actor_id):
    if user_id == actor_id and not active:
        raise ValidationError("Você não pode desativar a própria conta.")
    execute("UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?", (1 if active else 0, now(), user_id))
    audit(actor_id, "user", user_id, "activate" if active else "deactivate")


def set_staff(user_id, staff, actor_id):
    if user_id == actor_id and not staff:
        raise ValidationError("Você não pode remover o próprio acesso de administrador.")
    execute("UPDATE users SET is_staff = ?, updated_at = ? WHERE id = ?", (1 if staff else 0, now(), user_id))
    audit(actor_id, "user", user_id, "grant_staff" if staff else "revoke_staff")


def list_users(search="", status="", sort="recentes"):
    sql = """SELECT u.id, u.email, u.is_active, u.is_staff, u.created_at, u.last_login,
                    p.first_name, p.last_name, p.phone_number,
                    (SELECT COUNT(*) FROM orders o WHERE o.profile_id = p.id) AS orders_count
             FROM users u JOIN profiles p ON p.user_id = u.id WHERE u.deleted_at IS NULL"""
    params = []
    if search:
        sql += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR u.email LIKE ?)"
        params += [f"%{search}%"] * 3
    if status == "ativos":
        sql += " AND u.is_active = 1"
    elif status == "inativos":
        sql += " AND u.is_active = 0"
    elif status == "admins":
        sql += " AND u.is_staff = 1"
    order = {"recentes": "u.created_at DESC, u.id DESC", "antigos": "u.created_at ASC, u.id ASC",
             "nome": "p.first_name COLLATE NOCASE, p.last_name COLLATE NOCASE"}.get(sort, "u.id DESC")
    return query(sql + f" ORDER BY {order}", params)


def count_users():
    return query("SELECT COUNT(*) c FROM users WHERE deleted_at IS NULL", one=True)["c"]

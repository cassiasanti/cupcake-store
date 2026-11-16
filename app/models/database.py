"""Camada de acesso ao banco (SQLite) e utilitários comuns dos Models."""
import os
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class ValidationError(Exception):
    """Erro de regra de negócio / validação, exibido ao usuário."""


def now():
    """Timestamp em UTC (mesmo padrão do CURRENT_TIMESTAMP do SQLite)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=(), commit=True):
    db = get_db()
    cur = db.execute(sql, params)
    if commit:
        db.commit()
    return cur.lastrowid


def audit(user_id, entity, entity_id, action, details=""):
    execute(
        "INSERT INTO audit_logs (user_id, entity, entity_id, action, details) VALUES (?,?,?,?,?)",
        (user_id, entity, entity_id, action, details),
    )


def init_db(seed=True):
    db = get_db()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()
    if seed:
        from .seed import seed_data
        seed_data()

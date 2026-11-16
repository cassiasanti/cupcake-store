"""Utilitários compartilhados pelos Controllers."""
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from ..models import user as user_model


def current_user():
    if "user" not in g:
        uid = session.get("user_id")
        u = user_model.get_user(uid) if uid else None
        if u is not None and not u["is_active"]:
            session.clear()
            u = None
        g.user = u
    return g.user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Faça login para continuar.", "info")
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("auth.login", next=request.full_path))
        if not user["is_staff"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def safe_next(target, default):
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return default

"""Controller de autenticação (HU-001 Criar conta, HU-002 Login)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import user as user_model
from ..models.database import ValidationError
from .helpers import current_user, safe_next

bp = Blueprint("auth", __name__)


@bp.route("/registro", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("shop.index"))
    form = request.form
    if request.method == "POST":
        try:
            uid = user_model.create_user(form.get("first_name"), form.get("last_name"), form.get("email"),
                                         form.get("password", ""), form.get("confirm", ""))
            session.clear()
            session["user_id"] = uid
            session.permanent = True
            user_model.authenticate(form.get("email"), form.get("password"))
            flash("Conta criada com sucesso! Bem-vindo(a) à Cupcake Store. 🧁", "success")
            return redirect(url_for("profile.panel"))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("shop.index"))
    if request.method == "POST":
        try:
            uid = user_model.authenticate(request.form.get("email"), request.form.get("password"))
            session.clear()
            session["user_id"] = uid
            session.permanent = True
            user = user_model.get_user(uid)
            flash(f"Olá, {user['first_name']}!", "success")
            default = url_for("admin.dashboard") if user["is_staff"] else url_for("shop.index")
            return redirect(safe_next(request.args.get("next"), default))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("auth/login.html", email=request.form.get("email", ""))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))

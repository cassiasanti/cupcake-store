"""Controller do painel do usuário e perfil (HU-003, HU-009)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..models import order as order_model
from ..models import user as user_model
from ..models.database import ValidationError
from .helpers import current_user, login_required

bp = Blueprint("profile", __name__, url_prefix="/minha-conta")


@bp.route("/")
@login_required
def panel():
    user = current_user()
    orders = order_model.list_for_profile(user["profile_id"])
    active = [o for o in orders if o["status"] not in ("entregue", "cancelado")]
    spent = sum(o["total"] for o in orders if o["status"] not in ("cancelado", "aguardando_pagamento"))
    return render_template("profile/panel.html", user=user, recent=orders[:5], active=active,
                           total_orders=len(orders), spent=spent)


@bp.route("/perfil", methods=["GET", "POST"])
@login_required
def edit():
    user = current_user()
    form = request.form if request.method == "POST" else user
    if request.method == "POST":
        try:
            user_model.update_profile(user["id"], request.form)
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for("profile.edit"))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("profile/edit.html", form=form)


@bp.route("/conta", methods=["GET", "POST"])
@login_required
def account():
    user = current_user()
    if request.method == "POST":
        try:
            if request.form.get("action") == "email":
                user_model.update_email(user["id"], request.form.get("email"))
                flash("E-mail atualizado.", "success")
            else:
                user_model.change_password(user["id"], request.form.get("current"),
                                           request.form.get("new"), request.form.get("confirm"))
                flash("Senha alterada com sucesso.", "success")
            return redirect(url_for("profile.account"))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("profile/account.html", user=user)

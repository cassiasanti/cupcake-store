"""Controller do carrinho (HU-010 revisar, HU-011 adicionar, HU-012 remover)."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from ..models import cart as cart_model
from ..models.database import ValidationError
from .helpers import current_user, login_required, safe_next

bp = Blueprint("cart", __name__, url_prefix="/carrinho")


def _wants_json():
    return request.headers.get("X-Requested-With") == "fetch"


@bp.route("/")
@login_required
def view():
    user = current_user()
    cart = cart_model.open_cart(user["profile_id"])
    items = cart_model.items(cart["id"])
    total = cart_model.recalc(cart["id"])
    return render_template("cart/view.html", items=items, total=total)


@bp.route("/adicionar/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    user = current_user()
    try:
        product = cart_model.add(user["profile_id"], product_id, request.form.get("quantity", 1))
        msg = f"'{product['name']}' adicionado ao carrinho!"
        if _wants_json():
            return jsonify(ok=True, message=msg, count=cart_model.count(user["profile_id"]))
        flash(msg, "success")
    except ValidationError as e:
        if _wants_json():
            return jsonify(ok=False, message=str(e)), 400
        flash(str(e), "error")
    return redirect(safe_next(request.form.get("next"), url_for("shop.index")))


@bp.route("/item/<int:item_id>/quantidade", methods=["POST"])
@login_required
def update(item_id):
    try:
        cart_model.update_quantity(current_user()["profile_id"], item_id, request.form.get("quantity"))
        flash("Quantidade atualizada.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    return redirect(url_for("cart.view"))


@bp.route("/item/<int:item_id>/remover", methods=["POST"])
@login_required
def remove(item_id):
    try:
        name = cart_model.remove(current_user()["profile_id"], item_id)
        flash(f"'{name}' removido do carrinho.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    return redirect(url_for("cart.view"))

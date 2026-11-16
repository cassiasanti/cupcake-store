"""Controller de pedidos do cliente (HU-004..008)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..models import order as order_model
from ..models import store_config
from ..models.database import ValidationError
from .helpers import current_user, login_required

bp = Blueprint("orders", __name__)


def pix_qr_svg(payload):
    """QR Code em SVG (biblioteca opcional 'qrcode'); sem ela, mostra só o copia e cola."""
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        return None
    img = qrcode.make(payload, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    return img.to_string(encoding="unicode")


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user = current_user()
    cfg = store_config.get()
    methods = store_config.payment_methods()
    has_address = bool(user["address"] and user["city"] and user["postal_code"])
    default_delivery = "1" if (cfg["delivery_is_active"] and has_address) else "0"
    is_delivery = request.values.get("delivery", default_delivery) == "1"
    payment = request.values.get("payment", methods[0][0] if methods else "")
    if request.method == "POST":
        try:
            order_id = order_model.checkout(user, payment, is_delivery)
            flash("Pedido realizado com sucesso!", "success")
            return redirect(url_for("orders.detail", order_id=order_id, novo=1))
        except ValidationError as e:
            flash(str(e), "error")
    s = order_model.summary(user["profile_id"], is_delivery)
    if not s["items"]:
        flash("Seu carrinho está vazio.", "info")
        return redirect(url_for("shop.index"))
    return render_template("orders/checkout.html", s=s, methods=methods, payment=payment,
                           is_delivery=is_delivery, user=user, has_address=has_address)


@bp.route("/pedidos")
@login_required
def history():
    orders = order_model.list_for_profile(current_user()["profile_id"])
    return render_template("orders/list.html", orders=orders)


@bp.route("/pedidos/<int:order_id>")
@login_required
def detail(order_id):
    order = order_model.get(order_id, current_user()["profile_id"])
    if not order:
        abort(404)
    return render_template("orders/detail.html", order=order, items=order_model.order_items(order_id),
                           history=order_model.status_history(order_id), flow=order_model.FLOW,
                           can_cancel=order_model.can_cancel(order), novo=request.args.get("novo"),
                           qr=pix_qr_svg(order["pix_string"]) if order["status"] == "aguardando_pagamento"
                           and order["pix_string"] else None)


@bp.route("/pedidos/<int:order_id>/pagar", methods=["POST"])
@login_required
def pay(order_id):
    try:
        order_model.confirm_pix_payment(order_id, current_user()["profile_id"])
        flash("Pagamento confirmado! Seu pedido já está na fila de preparo.", "success")
    except ValidationError as e:
        flash(str(e), "error")
    return redirect(url_for("orders.detail", order_id=order_id))


@bp.route("/pedidos/<int:order_id>/cancelar", methods=["POST"])
@login_required
def cancel(order_id):
    try:
        refund = order_model.cancel(order_id, current_user()["profile_id"])
        msg = "Pedido cancelado."
        if refund:
            msg += " O reembolso do Pix foi solicitado e será creditado em até 2 dias úteis."
        flash(msg, "success")
    except ValidationError as e:
        flash(str(e), "error")
    return redirect(url_for("orders.detail", order_id=order_id))

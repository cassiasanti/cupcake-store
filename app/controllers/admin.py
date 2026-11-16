"""Controller da área administrativa (HU-013 a HU-019)."""
import os
import uuid

from flask import (Blueprint, abort, current_app, flash, redirect, render_template, request,
                   url_for)

from ..models import order as order_model
from ..models import product as product_model
from ..models import stock as stock_model
from ..models import store_config
from ..models import user as user_model
from ..models.database import ValidationError, query
from .helpers import admin_required, current_user

bp = Blueprint("admin", __name__, url_prefix="/admin")
ALLOWED_IMG = {"png", "jpg", "jpeg", "webp", "gif", "svg"}


@bp.route("/")
@admin_required
def dashboard():
    stats = order_model.stats()
    return render_template(
        "admin/dashboard.html", stats=stats, users=user_model.count_users(),
        products=product_model.count_products(), low_stock=stock_model.low_stock(),
        recent=order_model.list_all()[:6], sales=order_model.sales_last_days(7),
    )


# ------------------------------------------------------------------ Pedidos
@bp.route("/pedidos")
@admin_required
def orders():
    a = request.args
    rows = order_model.list_all(a.get("status", ""), a.get("q", "").strip(), a.get("sort", "recentes"),
                                a.get("de", ""), a.get("ate", ""), only_sales=a.get("vendas") == "1")
    return render_template("admin/orders.html", orders=rows, args=a)


@bp.route("/pedidos/<int:order_id>", methods=["GET", "POST"])
@admin_required
def order_detail(order_id):
    order = order_model.get(order_id)
    if not order:
        abort(404)
    if request.method == "POST":
        try:
            refund = order_model.admin_update_status(order_id, request.form.get("status"), current_user()["id"])
            flash("Status atualizado." + (" Reembolso Pix necessário." if refund else ""), "success")
        except ValidationError as e:
            flash(str(e), "error")
        return redirect(url_for("admin.order_detail", order_id=order_id))
    return render_template("admin/order_detail.html", order=order, items=order_model.order_items(order_id),
                           history=order_model.status_history(order_id),
                           next_status=order_model.TRANSITIONS[order["status"]])


# ------------------------------------------------------------------ Usuários
@bp.route("/usuarios")
@admin_required
def users():
    a = request.args
    return render_template("admin/users.html", users=user_model.list_users(a.get("q", "").strip(),
                           a.get("status", ""), a.get("sort", "recentes")), args=a)


@bp.route("/usuarios/novo", methods=["GET", "POST"])
@admin_required
def user_new():
    form = request.form
    if request.method == "POST":
        try:
            uid = user_model.create_user(form.get("first_name"), form.get("last_name"), form.get("email"),
                                         form.get("password", ""), form.get("confirm", ""),
                                         is_staff=bool(form.get("is_staff")), actor_id=current_user()["id"])
            flash("Usuário criado com sucesso.", "success")
            return redirect(url_for("admin.user_detail", user_id=uid))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("admin/user_form.html", form=form)


@bp.route("/usuarios/<int:user_id>", methods=["GET", "POST"])
@admin_required
def user_detail(user_id):
    u = user_model.get_user(user_id)
    if not u:
        abort(404)
    actor = current_user()["id"]
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "profile":
                user_model.update_profile(user_id, request.form, actor_id=actor)
                user_model.update_email(user_id, request.form.get("email"), actor_id=actor)
                flash("Dados do usuário atualizados.", "success")
            elif action == "toggle_active":
                user_model.set_active(user_id, not u["is_active"], actor)
                flash("Conta " + ("desativada." if u["is_active"] else "ativada."), "success")
            elif action == "toggle_staff":
                user_model.set_staff(user_id, not u["is_staff"], actor)
                flash("Permissão de administrador atualizada.", "success")
            elif action == "reset_password":
                user_model.admin_reset_password(user_id, request.form.get("new_password", ""), actor)
                flash("Senha redefinida.", "success")
        except ValidationError as e:
            flash(str(e), "error")
        return redirect(url_for("admin.user_detail", user_id=user_id))
    logs = query("""SELECT a.*, p.first_name FROM audit_logs a LEFT JOIN profiles p ON p.user_id = a.user_id
                    WHERE entity='user' AND entity_id=? ORDER BY a.id DESC LIMIT 20""", (user_id,))
    return render_template("admin/user_detail.html", u=u, orders=order_model.list_for_profile(u["profile_id"]),
                           logs=logs)


# ------------------------------------------------------------------ Produtos
def _save_upload():
    file = request.files.get("image_file")
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMG:
        raise ValidationError("Imagem inválida. Use PNG, JPG, WEBP, GIF ou SVG.")
    name = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return url_for("static", filename=f"uploads/{name}")


@bp.route("/produtos")
@admin_required
def products():
    a = request.args
    return render_template("admin/products.html",
                           products=product_model.list_admin(a.get("q", "").strip(), a.get("sort", "nome")), args=a)


@bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_required
def product_new():
    form = request.form
    if request.method == "POST":
        try:
            data = form.to_dict()
            data["image"] = _save_upload() or data.get("image_url") or "/static/img/products/baunilha.svg"
            pid = product_model.create(data, current_user()["id"])
            qty = form.get("initial_stock", "0").strip() or "0"
            if int(qty) > 0:
                stock_model.move(pid, "entrada", qty, current_user()["profile_id"], "Estoque inicial")
            flash("Produto cadastrado e publicado no catálogo.", "success")
            return redirect(url_for("admin.products"))
        except ValueError:
            flash("Estoque inicial inválido.", "error")
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("admin/product_form.html", form=form, product=None, flavors=product_model.FLAVORS)


@bp.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    product = product_model.get(product_id, include_inactive=True)
    if not product:
        abort(404)
    form = request.form if request.method == "POST" else product
    if request.method == "POST":
        try:
            data = request.form.to_dict()
            data["image"] = _save_upload() or data.get("image_url") or product["image"]
            data.setdefault("is_active", "0")
            changes = product_model.update(product_id, data, current_user()["id"])
            flash("Produto atualizado." if changes else "Nenhuma alteração detectada.", "success")
            return redirect(url_for("admin.product_edit", product_id=product_id))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("admin/product_form.html", form=form, product=product,
                           flavors=product_model.FLAVORS, history=product_model.history(product_id))


@bp.route("/produtos/<int:product_id>/excluir", methods=["POST"])
@admin_required
def product_delete(product_id):
    product = product_model.get(product_id, include_inactive=True)
    if not product:
        abort(404)
    if request.form.get("confirm_name", "").strip() != product["name"]:
        flash("Confirmação incorreta: digite o nome exato do produto para excluir.", "error")
        return redirect(url_for("admin.products"))
    product_model.delete(product_id, current_user()["id"])
    flash(f"'{product['name']}' excluído do catálogo.", "success")
    return redirect(url_for("admin.products"))


# ------------------------------------------------------------------ Estoque
@bp.route("/estoque", methods=["GET", "POST"])
@admin_required
def stock():
    products = product_model.list_admin()
    selected_id = request.values.get("product_id", type=int) or (products[0]["id"] if products else None)
    if request.method == "POST":
        try:
            new = stock_model.move(selected_id, request.form.get("type"), request.form.get("quantity"),
                                   current_user()["profile_id"], request.form.get("note", "").strip())
            flash(f"Movimentação registrada. Estoque atual: {new}.", "success")
        except ValidationError as e:
            flash(str(e), "error")
        return redirect(url_for("admin.stock", product_id=selected_id))
    selected = product_model.get(selected_id, include_inactive=True) if selected_id else None
    return render_template("admin/stock.html", products=products, selected=selected,
                           movements=stock_model.movements(selected_id)[:10] if selected_id else [])


@bp.route("/estoque/movimentacoes")
@admin_required
def movements():
    a = request.args
    return render_template("admin/movements.html", products=product_model.list_admin(),
                           movements=stock_model.movements(a.get("product_id", type=int), a.get("type", "")), args=a)


# ------------------------------------------------------------------ Configurações
@bp.route("/configuracoes/<section>", methods=["GET", "POST"])
@admin_required
def config(section):
    handlers = {"endereco": store_config.update_address, "pagamento": store_config.update_payment,
                "entrega": store_config.update_delivery}
    if section not in handlers:
        abort(404)
    if request.method == "POST":
        try:
            handlers[section](request.form, current_user()["id"])
            flash("Configurações salvas e aplicadas à loja.", "success")
            return redirect(url_for("admin.config", section=section))
        except ValidationError as e:
            flash(str(e), "error")
    return render_template("admin/config.html", section=section, cfg=store_config.get(),
                           key_types=store_config.PIX_KEY_TYPES)

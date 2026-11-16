"""Controller da vitrine / loja (catálogo público e detalhes do produto)."""
from flask import Blueprint, abort, render_template, request

from ..models import product as product_model

bp = Blueprint("shop", __name__)


@bp.route("/")
def index():
    flavor = request.args.get("sabor", "")
    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    catalog = product_model.list_catalog(flavor, search, page)
    return render_template("shop/index.html", catalog=catalog, flavor=flavor, search=search,
                           flavors=product_model.available_flavors())


@bp.route("/produto/<int:product_id>")
def detail(product_id):
    product = product_model.get(product_id)
    if not product:
        abort(404)
    return render_template("shop/detail.html", product=product)

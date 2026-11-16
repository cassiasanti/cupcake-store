"""Cupcake Store - aplicação Flask (padrão MVC).

Models      -> app/models      (regras de negócio + acesso ao SQLite)
Views       -> app/templates   (HTML/Jinja2) + app/static (CSS/JS)
Controllers -> app/controllers (Blueprints Flask: rotas e fluxo)
"""
import os
import secrets
from datetime import datetime, timedelta

from flask import Flask, abort, render_template, request, session

from .models import database


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-troque-esta-chave"),
        DATABASE=os.path.join(app.instance_path, "cupcake_store.sqlite"),
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH=3 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        WTF_CSRF_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.teardown_appcontext(database.close_db)

    with app.app_context():
        db_path = app.config["DATABASE"]
        if db_path == ":memory:" or not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            database.init_db(seed=app.config.get("SEED", True))

    @app.cli.command("init-db")
    def init_db_command():
        """Recria o banco de dados com dados de demonstração."""
        if os.path.exists(app.config["DATABASE"]):
            os.remove(app.config["DATABASE"])
        database.init_db()
        print("Banco de dados criado.")

    # -------------------------------------------------- Segurança: CSRF simples
    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    @app.before_request
    def check_csrf():
        if request.method == "POST" and app.config.get("WTF_CSRF_ENABLED", True):
            token = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
            if not token or token != session.get("_csrf"):
                abort(400, description="Sessão expirada. Recarregue a página e tente novamente.")

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    # -------------------------------------------------- Filtros de template
    @app.template_filter("brl")
    def brl(value):
        v = f"{float(value or 0):,.2f}"
        return "R$ " + v.replace(",", "X").replace(".", ",").replace("X", ".")

    @app.template_filter("dt")
    def dt(value, fmt="%d/%m/%Y %H:%M"):
        if not value:
            return "—"
        try:
            d = datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
        # created_at gravado pelo SQLite (UTC) -> horário de Brasília
        if len(str(value)) >= 19:
            d = d - timedelta(hours=3)
        return d.strftime(fmt)

    from .controllers import admin, auth, cart, orders, profile, shop
    from .controllers.helpers import current_user
    from .models import cart as cart_model
    from .models import order as order_model
    from .models import store_config

    app.jinja_env.globals.update(csrf_token=csrf_token, STATUS_LABELS=order_model.STATUS_LABELS)

    @app.context_processor
    def inject_globals():
        user = current_user()
        return {
            "current_user": user,
            "cart_count": cart_model.count(user["profile_id"]) if user else 0,
            "store": store_config.get(),
        }

    for bp in (auth.bp, shop.bp, cart.bp, orders.bp, profile.bp, admin.bp):
        app.register_blueprint(bp)

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/error.html", code=400, message=e.description), 400

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/error.html", code=403,
                               message="Você não tem permissão para acessar esta página."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/error.html", code=404, message="Página não encontrada."), 404

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("errors/error.html", code=413, message="Arquivo muito grande (máx. 3 MB)."), 413

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/error.html", code=500,
                               message="Ops! Algo deu errado. Tente novamente em instantes."), 500

    return app

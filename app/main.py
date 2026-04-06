import logging
import os

from flask import Flask, redirect, send_from_directory

from app.database import db
from app.extensions import limiter
from app.migrate_db import run_schema_patches

# Importação dos Blueprints
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.agendamentos import agendamentos_bp


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "../static"),
        template_folder=os.path.join(base_dir, "../templates"),
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from flask_cors import CORS

    CORS(app)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "phd_sao_braz_2026_key")

    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{os.path.join(project_root, 'app.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    limiter.init_app(app)

    # Migrações versionadas (opcional): mkdir migrations_phd && flask --app app.main db init
    mig_dir = os.path.join(project_root, "migrations_phd")
    if os.path.isdir(mig_dir):
        try:
            from flask_migrate import Migrate

            Migrate(app, db, directory=mig_dir)
        except Exception:
            pass

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(agendamentos_bp, url_prefix="/agendamentos")

    @app.route("/")
    def index():
        return send_from_directory(app.template_folder, "index.html")

    @app.route("/login")
    def login_page():
        return send_from_directory(app.template_folder, "login.html")

    @app.route("/admin")
    @app.route("/admin-page")
    def admin_page():
        return send_from_directory(app.template_folder, "admin.html")

    @app.route("/static/<path:path>")
    def send_static(path):
        return send_from_directory(app.static_folder, path)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "lash-agendamento"}, 200

    @app.route("/chat")
    def chat_page():
        return redirect("/", code=302)

    with app.app_context():
        from app.models import Usuario, Servico
        from app.auth import get_password_hash

        db.create_all()
        try:
            run_schema_patches(db)
        except Exception as exc:
            logging.getLogger("phd.main").exception("migrate: %s", exc)

        admin_existente = Usuario.query.filter_by(username="admin").first()
        if not admin_existente:
            novo_admin = Usuario(
                username="admin",
                role="admin",
                password_hash=get_password_hash("admin123"),
            )
            db.session.add(novo_admin)
            db.session.commit()
            logging.getLogger("phd.main").warning(
                "Admin padrao criado: admin / admin123 — altere a senha no painel."
            )
        else:
            logging.getLogger("phd.main").info("Banco e admin verificados.")

        if Servico.query.count() == 0:
            seeds = [
                ("Fio a Fio Clássico", 12000, 120, "/static/img/classico.jpg", 1),
                ("Volume Russo", 18000, 120, "/static/img/russo.jpg", 2),
                ("Lash Lifting", 9000, 90, "/static/img/lifting.jpg", 3),
            ]
            for nome, cents, dur, img, ordem in seeds:
                db.session.add(
                    Servico(
                        nome=nome,
                        preco_centavos=cents,
                        duracao_minutos=dur,
                        imagem_path=img,
                        ordem=ordem,
                        ativo=True,
                    )
                )
            db.session.commit()
            logging.getLogger("phd.main").info("Servicos padrao inseridos.")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    logging.getLogger("phd.main").info("Servidor em http://127.0.0.1:%s", port)
    app.run(host="0.0.0.0", port=port, debug=debug_mode)

import os
from flask import Flask, render_template
from flask_cors import CORS
from app.database import db
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.agendamentos import agendamentos_bp

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')

    CORS(app)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chave_secreta_padrao")
    
    # Configuração do Banco de Dados
    uri = os.getenv("DATABASE_URL", "sqlite:///../app.db")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Rotas para servir o Frontend
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/admin-painel') # Alterado para não conflitar com o prefixo da API
    def admin_page():
        return render_template('admin.html')

    # Registro das APIs
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(agendamentos_bp, url_prefix="/agendamentos")

    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from app.database import db

# Importação dos Blueprints
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.agendamentos import agendamentos_bp

def create_app():
    # Determinamos o caminho base para garantir que templates/static sejam encontrados
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Configuramos as pastas subindo um nível (..) pois a main está dentro de /app
    app = Flask(__name__, 
                static_folder=os.path.join(base_dir, '../static'), 
                template_folder=os.path.join(base_dir, '../templates'))

    # Configurações de Segurança e CORS
    CORS(app)
    
    # Chave secreta (usa variável de ambiente no deploy ou fallback local)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "phd_sao_braz_2026_key")

    # CONFIGURAÇÃO DE BANCO DE DADOS DINÂMICA (ESSENCIAL PARA DEPLOY)
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Se não houver DATABASE_URL, cria o SQLite local na raiz do projeto
    # O caminho absoluto evita que o SQLite crie o banco no lugar errado
    project_root = os.path.abspath(os.path.join(base_dir, '..'))
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{os.path.join(project_root, 'app.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicialização do Banco de Dados
    db.init_app(app)

    # Registro das Rotas de API (Blueprints)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(agendamentos_bp, url_prefix="/agendamentos")

    # --- ROTAS DE INTERFACE PARA O DEPLOY ---
    
    @app.route('/')
    def index():
        """Serve a página de login na raiz"""
        return send_from_directory(app.template_folder, 'login.html')

    @app.route('/admin')
    @app.route('/admin-page')
    def admin_page():
        """Serve a página administrativa. Suporta /admin ou /admin-page"""
        return send_from_directory(app.template_folder, 'admin.html')

    @app.route('/static/<path:path>')
    def send_static(path):
        """Serve arquivos estáticos (CSS, JS, Imagens)"""
        return send_from_directory(app.static_folder, path)

    # --- INICIALIZAÇÃO DO CONTEXTO (Criação de Tabelas e Admin) ---
    with app.app_context():
        # Importações internas para evitar 'Circular Import Error'
        from app.models import Usuario
        from app.auth import get_password_hash
        
        db.create_all()
        
        # Lógica para Criar admin padrão se o banco estiver vazio
        admin_existente = Usuario.query.filter_by(username="admin").first()
        if not admin_existente:
            novo_admin = Usuario(
                username="admin", 
                role="admin",
                password_hash=get_password_hash("admin123")
            )
            db.session.add(novo_admin)
            db.session.commit()
            print("✅ [SISTEMA] Admin padrão configurado: user: admin | pass: admin123")
        else:
            print("--- [SISTEMA] Banco de Dados e Admin verificados com sucesso ---")

    @app.route('/chat')
    def chat_page():
        return send_from_directory(app.template_folder, 'index.html')
    
    return app


# Instância global para o servidor WSGI (Necessário para Gunicorn no deploy)
app = create_app()

if __name__ == "__main__":
    # Porta dinâmica para plataformas de nuvem (Azure/Heroku/Render)
    port = int(os.environ.get("PORT", 8000))
    
    # Modo debug ativado apenas em desenvolvimento
    # Para ativar, use no terminal: set FLASK_ENV=development
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 Servidor PHP São Braz rodando em http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
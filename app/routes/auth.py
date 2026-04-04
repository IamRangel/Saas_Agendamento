from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from jose import jwt
from app.database import db
from app.models import Usuario
from app.auth import SECRET, ALGORITHM # Importa as configurações do seu app/auth.py

auth_bp = Blueprint("auth", __name__)

def create_access_token(data: dict):
    """Função auxiliar para gerar o Token JWT"""
    to_encode = data.copy()
    # Token expira em 24 horas
    expire = datetime.utcnow() + timedelta(minutes=1440)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # Validação básica de entrada
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"erro": "Usuário e senha são obrigatórios"}), 400

    # Busca o usuário no banco de dados (PostgreSQL/SQLite)
    usuario = Usuario.query.filter_by(username=data["username"]).first()

    # Verifica se o usuário existe e se a senha (hash) coincide
    if not usuario or not check_password_hash(usuario.password, data["password"]):
        return jsonify({"erro": "Credenciais inválidas"}), 401

    # Gera o token JWT com os dados do usuário
    token = create_access_token({
        "sub": usuario.username,
        "role": usuario.role
    })

    # Retorna o token no formato esperado pelo seu script JS (data.access_token)
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": usuario.username,
            "role": usuario.role
        }
    }), 200
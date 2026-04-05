from flask import Blueprint, request, jsonify
from app.database import db  # Importamos o db global em vez do SessionLocal
from app.models import Usuario
from app.auth import create_token, verify_password, get_password_hash
import datetime

# Definindo o Blueprint
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    try:
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"erro": "Dados incompletos"}), 400

        # Verifica se o usuário já existe usando o db.session do Flask
        if Usuario.query.filter_by(username=data["username"]).first():
            return jsonify({"erro": "Usuário já existe"}), 400

        # Criando o novo usuário
        novo_usuario = Usuario(
            username=data["username"],
            role=data.get("role", "user")
        )
        # Usando o método que criamos no models.py para setar a senha
        novo_usuario.password_hash = get_password_hash(data["password"])

        db.session.add(novo_usuario)
        db.session.commit()
        return jsonify({"mensagem": "Usuário registrado com sucesso!"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao registrar: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    try:
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"erro": "Credenciais ausentes"}), 400

        # Busca o usuário usando a sintaxe do Flask-SQLAlchemy (mais estável)
        usuario = Usuario.query.filter_by(username=data["username"]).first()

        # LOG DE DEBUG (Aparecerá no seu terminal para confirmar se ele achou o user)
        if usuario:
            print(f"--- [LOGIN] Usuário encontrado: {usuario.username}")
        else:
            print(f"--- [LOGIN] Usuário NÃO encontrado: {data['username']}")

        # Verifica existência e valida a senha
        if not usuario or not verify_password(data["password"], usuario.password_hash):
            return jsonify({"erro": "Login ou senha inválidos"}), 401

        # GERAÇÃO DO TOKEN JWT
        # Nota: O tempo de expiração já é tratado dentro do create_token no nosso auth.py
        token = create_token({
            "sub": usuario.username,
            "role": usuario.role
        })

        return jsonify({
            "mensagem": "Login realizado com sucesso!",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": usuario.username,
                "role": usuario.role
            }
        }), 200

    except Exception as e:
        print(f"❌ Erro interno no Login: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor"}), 500

@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"mensagem": "Logout realizado (Elimine o token no frontend)"}), 200
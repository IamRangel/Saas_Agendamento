import logging

from flask import Blueprint, request, jsonify

from app.database import db
from app.models import Usuario
from app.auth import create_token, verify_password, get_password_hash, decode_token

log = logging.getLogger("phd.auth")

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


@auth_bp.route("/alterar-senha", methods=["POST"])
def alterar_senha():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"erro": "Token ausente."}), 401
    payload = decode_token(auth[7:].strip())
    if not payload:
        return jsonify({"erro": "Token inválido ou expirado."}), 401

    data = request.get_json() or {}
    atual = data.get("senha_atual") or ""
    nova = data.get("senha_nova") or ""
    if len(nova) < 6:
        return jsonify({"erro": "Nova senha deve ter pelo menos 6 caracteres."}), 400

    usuario = Usuario.query.filter_by(username=payload.get("sub")).first()
    if not usuario or not verify_password(atual, usuario.password_hash):
        return jsonify({"erro": "Senha atual incorreta."}), 400

    try:
        usuario.password_hash = get_password_hash(nova)
        db.session.commit()
        log.info("senha_alterada user=%s", usuario.username)
        return jsonify({"mensagem": "Senha alterada com sucesso."}), 200
    except Exception as e:
        db.session.rollback()
        log.exception("alterar_senha")
        return jsonify({"erro": str(e)}), 500
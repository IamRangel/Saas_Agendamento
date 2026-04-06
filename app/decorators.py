from functools import wraps

from flask import request, jsonify

from app.auth import decode_token


def token_admin_obrigatorio(f):
    """Exige Authorization: Bearer <JWT> com role admin."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"erro": "Token de acesso ausente."}), 401
        token = auth[7:].strip()
        payload = decode_token(token)
        if not payload:
            return jsonify({"erro": "Sessão expirada ou token inválido."}), 401
        if payload.get("role") != "admin":
            return jsonify({"erro": "Acesso restrito a administradores."}), 403
        request.admin_username = payload.get("sub")
        return f(*args, **kwargs)

    return decorated

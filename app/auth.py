import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Configurações globais
# No deploy, configure a variável de ambiente SECRET_KEY no painel da Azure/Render
SECRET_KEY = os.getenv("SECRET_KEY", "phd_sao_braz_2026_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

def get_password_hash(password: str):
    """
    Gera o hash da senha usando o método pbkdf2:sha256 do Werkzeug.
    Este método é estável e evita conflitos com o bcrypt no Python 3.14.
    """
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(plain_password, hashed_password):
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado no banco.
    """
    if not hashed_password:
        return False
    return check_password_hash(hashed_password, plain_password)

def create_token(data: dict):
    """
    Gera o token JWT de acesso com payload e tempo de expiração.
    """
    to_encode = data.copy()
    
    # Define a expiração baseada no UTC atual
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # O JWT espera o campo 'exp' para validação automática
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """
    Decodifica o token JWT e valida a assinatura e expiração.
    Retorna o payload se válido, ou None se houver erro ou expiração.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Aliases de compatibilidade para evitar erros em outros arquivos de rotas
hash_password = get_password_hash
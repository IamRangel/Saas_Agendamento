from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

# Configurações globais
SECRET_KEY = "SUA_CHAVE_SECRETA_PHD_2026"
SECRET = SECRET_KEY  # Alias para compatibilidade
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# O esquema OAuth2 que as rotas admin estavam procurando
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str):
    """Gera o hash da senha para salvar no banco"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """Verifica se a senha digitada bate com o hash do banco"""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict):
    """Gera o token JWT de acesso"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

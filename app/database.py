import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Instância do Flask-SQLAlchemy (O que o seu main.py tenta importar)
db = SQLAlchemy()

def get_database_url():
    """
    Retorna a URL do banco de dados tratada para Deploy ou Local.
    """
    url = os.getenv("DATABASE_URL")
    
    # Ajuste obrigatório para SQLAlchemy 2.0+ em serviços de nuvem (Heroku/Render/Azure)
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Driver Psycopg 3 (wheels amplos; evita build do psycopg2 em Python novo)
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Se não houver URL de ambiente, usa SQLite local
    return url or "sqlite:///app.db"

# 2. Configurações para uso fora do contexto do Flask (Scripts ou Migrações)
DATABASE_URL = get_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Função utilitária para dependência de banco em rotas
def get_db():
    """
    Garante que a conexão seja aberta e fechada corretamente por requisição.
    """
    connection = SessionLocal()
    try:
        yield connection
    finally:
        connection.close()
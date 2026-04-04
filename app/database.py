import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

db = SQLAlchemy()

# Pega a URL do Render ou usa SQLite local para testes
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Ajuste para compatibilidade do SQLAlchemy com URLs antigas do Postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
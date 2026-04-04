from app.database import db
from datetime import datetime


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Armazena o hash
    role = db.Column(db.String(20), default="user")  # 'admin' ou 'user'

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password = generate_password_hash(password, method="pbkdf2:sha256")


class Horario(db.Model):
    __tablename__ = "horarios"

    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False, unique=True)
    disponivel = db.Column(db.Boolean, default=True)

    # Relacionamento para facilitar a busca
    agendamentos = db.relationship(
        "Agendamento", backref="horario", lazy=True, cascade="all, delete-orphan"
    )


class Agendamento(db.Model):
    __tablename__ = "agendamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False, index=True)
    horario_id = db.Column(db.Integer, db.ForeignKey("horarios.id"), nullable=False)

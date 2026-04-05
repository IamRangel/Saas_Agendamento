from app.database import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # Alterado para password_hash para ser consistente com o main.py e auth.py
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # 'admin' ou 'user'

    def set_password(self, password):
        """Gera o hash da senha usando nossa lógica centralizada no auth.py"""
        from app.auth import get_password_hash
        self.password_hash = get_password_hash(password)

    def check_password(self, password):
        """Verifica a senha usando nossa lógica centralizada no auth.py"""
        from app.auth import verify_password
        return verify_password(password, self.password_hash)

    def __repr__(self):
        return f'<Usuario {self.username}>'


class Horario(db.Model):
    __tablename__ = "horarios"

    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False, unique=True)
    disponivel = db.Column(db.Boolean, default=True)

    # Relacionamento: permite acessar agendamentos a partir do objeto Horario
    # O cascade garante integridade se um horário for removido
    agendamentos = db.relationship(
        "Agendamento", 
        back_populates="horario", 
        lazy=True, 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<Horario {self.data_hora} | Disponível: {self.disponivel}>'


class Agendamento(db.Model):
    __tablename__ = "agendamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False, index=True)
    
    # Chave Estrangeira
    horario_id = db.Column(db.Integer, db.ForeignKey("horarios.id"), nullable=False)
    
    # Relacionamento reverso
    horario = db.relationship("Horario", back_populates="agendamentos")

    def __repr__(self):
        return f'<Agendamento {self.nome} - {self.telefone}>'
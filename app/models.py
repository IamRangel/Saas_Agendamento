from app.database import db
from datetime import date, datetime


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")

    def set_password(self, password):
        from app.auth import get_password_hash

        self.password_hash = get_password_hash(password)

    def check_password(self, password):
        from app.auth import verify_password

        return verify_password(password, self.password_hash)

    def __repr__(self):
        return f"<Usuario {self.username}>"


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco_centavos = db.Column(db.Integer, default=0)
    duracao_minutos = db.Column(db.Integer, default=60)
    imagem_path = db.Column(db.String(200), default="")
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Servico {self.nome}>"


class DiaBloqueado(db.Model):
    """Datas em que não se oferece agenda (folga/feriado)."""

    __tablename__ = "dias_bloqueados"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, unique=True, nullable=False)
    motivo = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<DiaBloqueado {self.data}>"


class Horario(db.Model):
    __tablename__ = "horarios"

    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False, unique=True)
    disponivel = db.Column(db.Boolean, default=True)
    intervalo_minutos = db.Column(db.Integer, default=60)

    agendamentos = db.relationship(
        "Agendamento",
        back_populates="horario",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Horario {self.data_hora} | Disponível: {self.disponivel}>"


class Agendamento(db.Model):
    __tablename__ = "agendamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False, index=True)
    horario_id = db.Column(db.Integer, db.ForeignKey("horarios.id"), nullable=False)
    tipo_servico = db.Column(db.String(120), nullable=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=True)
    duracao_minutos = db.Column(db.Integer, nullable=True)
    horarios_extra_ids = db.Column(db.Text, nullable=True)

    horario = db.relationship("Horario", back_populates="agendamentos")
    servico = db.relationship("Servico", backref="agendamentos_lista", lazy=True)

    def __repr__(self):
        return f"<Agendamento {self.nome} - {self.telefone}>"

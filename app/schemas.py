from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LoginSchema(BaseModel):
    username: str
    password: str


class HorarioCreate(BaseModel):
    data_hora: datetime


class AgendamentoCreate(BaseModel):
    nome: str
    telefone: str
    horario_id: int

"""Regras de ocupação de horários (múltiplos slots por duração do serviço)."""
from __future__ import annotations

import json
import math
from datetime import timedelta
from typing import List, Optional

from app.database import db
from app.models import Horario


def intervalo_do_horario(h: Horario) -> int:
    v = getattr(h, "intervalo_minutos", None) or 60
    return max(15, min(int(v), 240))


def coletar_slots_consecutivos_livres(
    horario_inicio_id: int, duracao_minutos: int
) -> Optional[List[Horario]]:
    """
    A partir do primeiro slot, exige N slots consecutivos (mesmo intervalo entre horários).
    Retorna lista [h0, h1, ...] ou None se indisponível.
    """
    h0 = db.session.get(Horario, horario_inicio_id)
    if not h0 or not h0.disponivel:
        return None

    intervalo = intervalo_do_horario(h0)
    qtd = max(1, math.ceil(duracao_minutos / intervalo))

    if qtd == 1:
        return [h0]

    esperados = [h0.data_hora + timedelta(minutes=intervalo * i) for i in range(qtd)]
    if h0.data_hora != esperados[0]:
        return None

    cadeia = [h0]
    for i in range(1, qtd):
        hi = Horario.query.filter_by(data_hora=esperados[i]).first()
        if not hi or not hi.disponivel:
            return None
        if intervalo_do_horario(hi) != intervalo:
            return None
        cadeia.append(hi)

    return cadeia


def ids_extras_json(cadeia: List[Horario]) -> Optional[str]:
    if len(cadeia) <= 1:
        return None
    return json.dumps([h.id for h in cadeia[1:]])


def parse_ids_extras(raw: Optional[str]) -> List[int]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [int(x) for x in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def liberar_todos_slots_agendamento(horario_principal_id: int, extras_json: Optional[str]):
    """Marca disponivel=True em todos os horários ligados ao agendamento."""
    ids = [horario_principal_id] + parse_ids_extras(extras_json)
    for hid in ids:
        h = db.session.get(Horario, hid)
        if h:
            h.disponivel = True


def ocupar_cadeia(cadeia: List[Horario]):
    for h in cadeia:
        h.disponivel = False


def liberar_agendamento_por_modelo(ag) -> None:
    """Recebe instância Agendamento (evita import circular aqui)."""
    liberar_todos_slots_agendamento(ag.horario_id, ag.horarios_extra_ids)


def filtrar_inicios_com_duracao(
    horarios_livres: List[Horario], duracao_minutos: int
) -> List[Horario]:
    """
    Dada lista de Horario livres ordenados por data_hora, devolve apenas os que podem
    iniciar um atendimento de duracao_minutos (cadeia inteira livre).
    """
    if duracao_minutos <= 0:
        duracao_minutos = 60

    by_dt = {h.data_hora: h for h in horarios_livres}
    sorted_times = sorted(by_dt.keys())
    valid_starts: List[Horario] = []

    for t in sorted_times:
        h0 = by_dt[t]
        intervalo = intervalo_do_horario(h0)
        qtd = max(1, math.ceil(duracao_minutos / intervalo))
        ok = True
        for i in range(qtd):
            need = t + timedelta(minutes=intervalo * i)
            hi = by_dt.get(need)
            if hi is None:
                ok = False
                break
            if intervalo_do_horario(hi) != intervalo:
                ok = False
                break
        if ok:
            valid_starts.append(h0)

    return valid_starts

"""Datas e horas no fuso de São Paulo (America/Sao_Paulo)."""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_BR = ZoneInfo("America/Sao_Paulo")


def agora_brasil() -> datetime:
    return datetime.now(TZ_BR)


def utc_para_brasil(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TZ_BR)

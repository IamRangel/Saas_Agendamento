"""Patches de schema para SQLite/Postgres sem Alembic obrigatório."""

from sqlalchemy import inspect, text


def _has_col(inspector, table: str, col: str) -> bool:
    try:
        cols = [c["name"] for c in inspector.get_columns(table)]
    except Exception:
        return False
    return col in cols


def run_schema_patches(db) -> None:
    inspector = inspect(db.engine)

    patches = []

    if inspector.has_table("horarios") and not _has_col(inspector, "horarios", "intervalo_minutos"):
        patches.append(
            "ALTER TABLE horarios ADD COLUMN intervalo_minutos INTEGER DEFAULT 60"
        )

    if inspector.has_table("agendamentos"):
        if not _has_col(inspector, "agendamentos", "tipo_servico"):
            patches.append(
                "ALTER TABLE agendamentos ADD COLUMN tipo_servico VARCHAR(120)"
            )
        if not _has_col(inspector, "agendamentos", "servico_id"):
            patches.append("ALTER TABLE agendamentos ADD COLUMN servico_id INTEGER")
        if not _has_col(inspector, "agendamentos", "duracao_minutos"):
            patches.append(
                "ALTER TABLE agendamentos ADD COLUMN duracao_minutos INTEGER"
            )
        if not _has_col(inspector, "agendamentos", "horarios_extra_ids"):
            patches.append(
                "ALTER TABLE agendamentos ADD COLUMN horarios_extra_ids TEXT"
            )

    for sql in patches:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

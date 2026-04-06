import logging
from datetime import date

from flask import Blueprint, request, jsonify

from app.database import db
from app.extensions import limiter
from app.models import Agendamento, Horario, Servico, DiaBloqueado
from app.agendamento_logic import (
    coletar_slots_consecutivos_livres,
    filtrar_inicios_com_duracao,
    ids_extras_json,
    liberar_agendamento_por_modelo,
    ocupar_cadeia,
)

log = logging.getLogger("phd.agendamentos")

agendamentos_bp = Blueprint("agendamentos", __name__)


def limpar_telefone(tel):
    if not tel:
        return ""
    return "".join(filter(str.isdigit, tel))


def _datas_bloqueadas():
    rows = DiaBloqueado.query.all()
    return {r.data for r in rows}


@agendamentos_bp.route("/servicos", methods=["GET"])
def listar_servicos_publicos():
    try:
        lista = (
            Servico.query.filter_by(ativo=True)
            .order_by(Servico.ordem, Servico.id)
            .all()
        )
        out = []
        for s in lista:
            out.append(
                {
                    "id": s.id,
                    "nome": s.nome,
                    "preco_centavos": s.preco_centavos,
                    "preco_reais": round(s.preco_centavos / 100, 2),
                    "duracao_minutos": s.duracao_minutos,
                    "imagem_path": s.imagem_path or "",
                }
            )
        return jsonify(out), 200
    except Exception as e:
        log.exception("listar_servicos")
        return jsonify({"erro": str(e)}), 500


@agendamentos_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    try:
        bloqueados = _datas_bloqueadas()
        modo_admin = (request.args.get("modo") or "").lower() == "admin"
        duracao = int(request.args.get("duracao_minutos", 60) or 60)

        horarios = (
            Horario.query.filter_by(disponivel=True)
            .order_by(Horario.data_hora)
            .all()
        )

        grade = {}
        for h in horarios:
            d = h.data_hora.date()
            if d in bloqueados:
                continue
            data_str = h.data_hora.strftime("%Y-%m-%d")
            if data_str not in grade:
                grade[data_str] = []
            grade[data_str].append(h)

        resultado = {}
        for data_str, lista_h in sorted(grade.items()):
            if modo_admin:
                validos = lista_h
            else:
                validos = filtrar_inicios_com_duracao(lista_h, duracao)
            resultado[data_str] = [
                {"id": h.id, "hora": h.data_hora.strftime("%H:%M")} for h in validos
            ]

        return jsonify(resultado), 200
    except Exception as e:
        log.exception("listar_horarios")
        return jsonify({"erro": str(e)}), 500


@agendamentos_bp.route("/verificar", methods=["GET"])
@limiter.limit("45 per minute")
def verificar_status():
    telefone_bruto = request.args.get("telefone", "")
    telefone = limpar_telefone(telefone_bruto)

    if not telefone:
        return (
            jsonify({"possui_agendamento": False, "erro": "Telefone não informado"}),
            400,
        )

    agendamento = Agendamento.query.filter_by(telefone=telefone).first()

    if agendamento:
        return (
            jsonify(
                {
                    "possui_agendamento": True,
                    "detalhes": {
                        "id": agendamento.id,
                        "data_hora": agendamento.horario.data_hora.isoformat(),
                        "nome": agendamento.nome,
                        "tipo_servico": agendamento.tipo_servico,
                        "duracao_minutos": agendamento.duracao_minutos,
                    },
                }
            ),
            200,
        )

    return jsonify({"possui_agendamento": False}), 200


@agendamentos_bp.route("/criar", methods=["POST"])
@limiter.limit("25 per minute")
def criar_agendamento():
    nome = (request.args.get("nome") or "").strip()
    telefone_bruto = request.args.get("telefone", "")
    horario_id = request.args.get("horario_id")
    tipo_servico = (request.args.get("servico") or "").strip() or None
    servico_id_arg = request.args.get("servico_id")

    telefone = limpar_telefone(telefone_bruto)

    if not all([nome, telefone, horario_id]):
        return jsonify({"erro": "Dados insuficientes para agendar"}), 400

    try:
        horario_id = int(horario_id)
    except (TypeError, ValueError):
        return jsonify({"erro": "horario_id inválido"}), 400

    servico = None
    if servico_id_arg:
        try:
            sid = int(servico_id_arg)
            servico = Servico.query.filter_by(id=sid, ativo=True).first()
        except (TypeError, ValueError):
            pass
    if servico is None and tipo_servico:
        servico = Servico.query.filter_by(nome=tipo_servico, ativo=True).first()

    duracao_min = servico.duracao_minutos if servico else 60
    nome_servico = servico.nome if servico else tipo_servico

    try:
        agendamento_antigo = Agendamento.query.filter_by(telefone=telefone).first()
        if agendamento_antigo:
            liberar_agendamento_por_modelo(agendamento_antigo)
            db.session.delete(agendamento_antigo)
            db.session.flush()

        cadeia = coletar_slots_consecutivos_livres(horario_id, duracao_min)
        if not cadeia:
            return (
                jsonify(
                    {
                        "erro": "Horário indisponível ou tempo insuficiente para este serviço. Escolha outro horário de início.",
                    }
                ),
                400,
            )

        d_dia = cadeia[0].data_hora.date()
        if d_dia in _datas_bloqueadas():
            return jsonify({"erro": "Esta data não está disponível para agendamento."}), 400

        ocupar_cadeia(cadeia)
        extras = ids_extras_json(cadeia)

        novo = Agendamento(
            nome=nome,
            telefone=telefone,
            horario_id=cadeia[0].id,
            tipo_servico=nome_servico,
            servico_id=servico.id if servico else None,
            duracao_minutos=duracao_min,
            horarios_extra_ids=extras,
        )
        db.session.add(novo)
        db.session.commit()

        log.info("agendamento_criado telefone=%s horario=%s", telefone, cadeia[0].id)
        return (
            jsonify(
                {
                    "mensagem": "Agendamento confirmado com sucesso!",
                    "id": novo.id,
                    "data_hora_inicio": cadeia[0].data_hora.isoformat(),
                    "data_hora_fim": cadeia[-1].data_hora.isoformat(),
                }
            ),
            201,
        )

    except Exception as e:
        log.exception("criar_agendamento")
        db.session.rollback()
        return jsonify({"erro": "Erro interno ao processar agendamento"}), 500


@agendamentos_bp.route("/cancelar", methods=["DELETE"])
@limiter.limit("15 per minute")
def cancelar_agendamento():
    telefone_bruto = request.args.get("telefone", "")
    telefone = limpar_telefone(telefone_bruto)

    agendamento = Agendamento.query.filter_by(telefone=telefone).first()

    if not agendamento:
        return jsonify({"erro": "Nenhum agendamento encontrado para este número"}), 404

    try:
        liberar_agendamento_por_modelo(agendamento)
        db.session.delete(agendamento)
        db.session.commit()
        log.info("agendamento_cancelado telefone=%s", telefone)
        return (
            jsonify({"mensagem": "Agendamento cancelado. O horário está livre."}),
            200,
        )
    except Exception as e:
        log.exception("cancelar_agendamento")
        db.session.rollback()
        return jsonify({"erro": "Erro ao cancelar agendamento"}), 500

import csv
import io
import logging
from calendar import monthrange
from datetime import datetime, timedelta

from flask import Blueprint, Response, request, jsonify
from sqlalchemy import and_, func

from app.auth import decode_token
from app.database import db
from app.models import Horario, Agendamento, Servico, DiaBloqueado
from app.agendamento_logic import liberar_agendamento_por_modelo
from app.util_time import agora_brasil

log = logging.getLogger("phd.admin")

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def _exigir_admin_jwt():
    if request.method == "OPTIONS":
        return None
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"erro": "Token de acesso ausente."}), 401
    token = auth[7:].strip()
    payload = decode_token(token)
    if not payload:
        return jsonify({"erro": "Sessão expirada ou token inválido."}), 401
    if payload.get("role") != "admin":
        return jsonify({"erro": "Acesso restrito a administradores."}), 403
    request.admin_username = payload.get("sub")
    return None


def _criar_slots_no_dia(data_alvo, inicio_str, fim_str, intervalo_min):
    formato = "%Y-%m-%d %H:%M"
    dia = datetime.strptime(data_alvo, "%Y-%m-%d").date()
    if DiaBloqueado.query.filter_by(data=dia).first():
        return 0

    horario_atual = datetime.strptime(f"{data_alvo} {inicio_str}", formato)
    horario_limite = datetime.strptime(f"{data_alvo} {fim_str}", formato)
    if horario_atual > horario_limite:
        return 0
    novos = 0
    while horario_atual <= horario_limite:
        existe = Horario.query.filter_by(data_hora=horario_atual).first()
        if not existe:
            db.session.add(
                Horario(
                    data_hora=horario_atual,
                    disponivel=True,
                    intervalo_minutos=intervalo_min,
                )
            )
            novos += 1
        else:
            if existe.intervalo_minutos != intervalo_min:
                existe.intervalo_minutos = intervalo_min
        horario_atual += timedelta(minutes=intervalo_min)
    return novos


@admin_bp.route("/dashboard", methods=["GET"])
def dashboard_resumo():
    try:
        hoje = agora_brasil().date()
        amanha = hoje + timedelta(days=1)

        def cnt_desde_ate(d0, d1):
            return (
                db.session.query(func.count(Agendamento.id))
                .join(Horario, Agendamento.horario_id == Horario.id)
                .filter(
                    func.date(Horario.data_hora) >= d0,
                    func.date(Horario.data_hora) < d1,
                )
                .scalar()
            )

        return (
            jsonify(
                {
                    "agendamentos_hoje": cnt_desde_ate(hoje, hoje + timedelta(days=1)),
                    "agendamentos_amanha": cnt_desde_ate(amanha, amanha + timedelta(days=1)),
                    "agendamentos_proximos_7_dias": cnt_desde_ate(
                        hoje, hoje + timedelta(days=7)
                    ),
                    "horarios_livres": Horario.query.filter_by(disponivel=True).count(),
                }
            ),
            200,
        )
    except Exception as e:
        log.exception("dashboard")
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/agendamentos", methods=["GET"])
def listar_agendamentos():
    try:
        agendamentos = (
            Agendamento.query.join(Horario, Agendamento.horario_id == Horario.id)
            .order_by(Horario.data_hora.asc())
            .all()
        )
        resultado = []
        for a in agendamentos:
            data_formatada = "Sem data"
            if a.horario:
                data_formatada = a.horario.data_hora.strftime("%d/%m/%Y %H:%M")
            resultado.append(
                {
                    "id": a.id,
                    "nome": a.nome,
                    "telefone": a.telefone,
                    "data_hora": data_formatada,
                    "data_hora_iso": (
                        a.horario.data_hora.isoformat() if a.horario else None
                    ),
                    "tipo_servico": a.tipo_servico or "",
                    "duracao_minutos": a.duracao_minutos,
                    "servico_id": a.servico_id,
                }
            )
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/agendamentos/export.csv", methods=["GET"])
def exportar_agendamentos_csv():
    try:
        rows = (
            Agendamento.query.join(Horario, Agendamento.horario_id == Horario.id)
            .order_by(Horario.data_hora.asc())
            .all()
        )
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(
            ["id", "data_hora", "nome", "telefone", "servico", "duracao_min"]
        )
        for a in rows:
            w.writerow(
                [
                    a.id,
                    a.horario.data_hora.isoformat() if a.horario else "",
                    a.nome,
                    a.telefone,
                    a.tipo_servico or "",
                    a.duracao_minutos or "",
                ]
            )
        out = buf.getvalue()
        return Response(
            out,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=agendamentos.csv",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/servicos", methods=["GET"])
def admin_listar_servicos():
    lista = Servico.query.order_by(Servico.ordem, Servico.id).all()
    return (
        jsonify(
            [
                {
                    "id": s.id,
                    "nome": s.nome,
                    "preco_centavos": s.preco_centavos,
                    "duracao_minutos": s.duracao_minutos,
                    "imagem_path": s.imagem_path or "",
                    "ordem": s.ordem,
                    "ativo": s.ativo,
                }
                for s in lista
            ]
        ),
        200,
    )


@admin_bp.route("/servicos", methods=["POST"])
def admin_criar_servico():
    data = request.get_json() or {}
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"erro": "Nome obrigatório"}), 400
    s = Servico(
        nome=nome,
        preco_centavos=int(data.get("preco_centavos", 0)),
        duracao_minutos=int(data.get("duracao_minutos", 60)),
        imagem_path=(data.get("imagem_path") or "").strip(),
        ordem=int(data.get("ordem", 0)),
        ativo=bool(data.get("ativo", True)),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"id": s.id, "mensagem": "Serviço criado"}), 201


@admin_bp.route("/servicos/<int:sid>", methods=["PUT"])
def admin_atualizar_servico(sid):
    s = Servico.query.get(sid)
    if not s:
        return jsonify({"erro": "Não encontrado"}), 404
    data = request.get_json() or {}
    if "nome" in data:
        s.nome = (data.get("nome") or "").strip() or s.nome
    if "preco_centavos" in data:
        s.preco_centavos = int(data["preco_centavos"])
    if "duracao_minutos" in data:
        s.duracao_minutos = int(data["duracao_minutos"])
    if "imagem_path" in data:
        s.imagem_path = (data.get("imagem_path") or "").strip()
    if "ordem" in data:
        s.ordem = int(data["ordem"])
    if "ativo" in data:
        s.ativo = bool(data["ativo"])
    db.session.commit()
    return jsonify({"mensagem": "Atualizado"}), 200


@admin_bp.route("/servicos/<int:sid>", methods=["DELETE"])
def admin_remover_servico(sid):
    s = Servico.query.get(sid)
    if not s:
        return jsonify({"erro": "Não encontrado"}), 404
    s.ativo = False
    db.session.commit()
    return jsonify({"mensagem": "Serviço desativado"}), 200


@admin_bp.route("/dias-bloqueados", methods=["GET"])
def listar_dias_bloqueados():
    rows = DiaBloqueado.query.order_by(DiaBloqueado.data).all()
    return (
        jsonify(
            [
                {
                    "id": r.id,
                    "data": r.data.isoformat(),
                    "motivo": r.motivo or "",
                }
                for r in rows
            ]
        ),
        200,
    )


@admin_bp.route("/dias-bloqueados", methods=["POST"])
def bloquear_dia():
    data = request.get_json() or {}
    ds = (data.get("data") or "").strip()
    if not ds:
        return jsonify({"erro": "Campo data (YYYY-MM-DD) obrigatório"}), 400
    try:
        d = datetime.strptime(ds, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"erro": "Data inválida"}), 400
    if DiaBloqueado.query.filter_by(data=d).first():
        return jsonify({"erro": "Data já bloqueada"}), 400
    r = DiaBloqueado(data=d, motivo=(data.get("motivo") or "").strip() or None)
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id, "mensagem": "Dia bloqueado"}), 201


@admin_bp.route("/dias-bloqueados/<ds>", methods=["DELETE"])
def desbloquear_dia(ds):
    try:
        d = datetime.strptime(ds, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"erro": "Data inválida"}), 400
    r = DiaBloqueado.query.filter_by(data=d).first()
    if not r:
        return jsonify({"erro": "Não encontrado"}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({"mensagem": "Dia liberado"}), 200


@admin_bp.route("/gerar-grade", methods=["POST", "OPTIONS"])
def gerar_grade_automatica():
    data_alvo = request.args.get("data")
    inicio_str = request.args.get("inicio")
    fim_str = request.args.get("fim")
    intervalo_min = int(request.args.get("intervalo", 60))

    if not all([data_alvo, inicio_str, fim_str]):
        return (
            jsonify({"erro": "Parâmetros 'data', 'inicio' e 'fim' são obrigatórios"}),
            400,
        )

    try:
        novos_horarios = _criar_slots_no_dia(
            data_alvo, inicio_str, fim_str, intervalo_min
        )
        db.session.commit()
        return (
            jsonify(
                {
                    "mensagem": "Grade gerada com sucesso!",
                    "quantidade_criada": novos_horarios,
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao processar datas: {str(e)}"}), 400


@admin_bp.route("/gerar-grade-mes", methods=["POST", "OPTIONS"])
def gerar_grade_mes_inteiro():
    try:
        ano = int(request.args.get("ano"))
        mes = int(request.args.get("mes"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Informe ano e mês válidos (números)."}), 400

    inicio_str = request.args.get("inicio")
    fim_str = request.args.get("fim")
    intervalo_min = int(request.args.get("intervalo", 60))

    if not all([inicio_str, fim_str]):
        return (
            jsonify({"erro": "Parâmetros 'inicio' e 'fim' são obrigatórios"}),
            400,
        )

    if mes < 1 or mes > 12:
        return jsonify({"erro": "Mês inválido (use 1 a 12)."}), 400

    _, ultimo_dia = monthrange(ano, mes)

    try:
        novos_total = 0
        for dia in range(1, ultimo_dia + 1):
            data_alvo = datetime(ano, mes, dia).strftime("%Y-%m-%d")
            novos_total += _criar_slots_no_dia(
                data_alvo, inicio_str, fim_str, intervalo_min
            )

        db.session.commit()
        return (
            jsonify(
                {
                    "mensagem": "Grade do mês gerada com sucesso!",
                    "quantidade_criada": novos_total,
                    "dias_processados": ultimo_dia,
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao processar: {str(e)}"}), 400


@admin_bp.route("/horarios/dia", methods=["DELETE"])
def excluir_horarios_livres_do_dia():
    data_str = request.args.get("data")
    if not data_str:
        return jsonify({"erro": "Parâmetro 'data' (YYYY-MM-DD) é obrigatório."}), 400

    try:
        dia_ini = datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"erro": "Data inválida. Use o formato YYYY-MM-DD."}), 400

    dia_fim = dia_ini + timedelta(days=1)

    try:
        livres = (
            Horario.query.filter(
                and_(
                    Horario.data_hora >= dia_ini,
                    Horario.data_hora < dia_fim,
                    Horario.disponivel.is_(True),
                )
            )
            .all()
        )

        ocupados = (
            Horario.query.filter(
                and_(
                    Horario.data_hora >= dia_ini,
                    Horario.data_hora < dia_fim,
                    Horario.disponivel.is_(False),
                )
            ).count()
        )

        for h in livres:
            db.session.delete(h)

        db.session.commit()
        return (
            jsonify(
                {
                    "mensagem": f"{len(livres)} horário(s) livre(s) removidos.",
                    "removidos": len(livres),
                    "horarios_com_agendamento": ocupados,
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/horarios/<int:horario_id>", methods=["DELETE"])
@admin_bp.route("/grade/<int:horario_id>", methods=["DELETE"])
def excluir_um_horario(horario_id):
    h = Horario.query.get(horario_id)
    if not h:
        return jsonify({"erro": "Horário não encontrado."}), 404
    if not h.disponivel:
        return (
            jsonify(
                {
                    "erro": "Este horário possui agendamento. Cancele o cliente na lista ao lado antes de remover.",
                }
            ),
            409,
        )
    try:
        db.session.delete(h)
        db.session.commit()
        return jsonify({"mensagem": "Horário removido."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/agendamentos/<int:agendamento_id>", methods=["DELETE"])
def excluir_agendamento_admin(agendamento_id):
    a = Agendamento.query.get(agendamento_id)
    if not a:
        return jsonify({"erro": "Agendamento não encontrado."}), 404
    try:
        liberar_agendamento_por_modelo(a)
        db.session.delete(a)
        db.session.commit()
        log.info("admin_cancela agendamento_id=%s", agendamento_id)
        return jsonify({"mensagem": "Agendamento cancelado."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/horarios/limpar", methods=["DELETE"])
def limpar_horarios_vazios():
    try:
        num_deletados = Horario.query.filter_by(disponivel=True).delete()
        db.session.commit()
        return jsonify({"mensagem": f"{num_deletados} horários vazios removidos."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

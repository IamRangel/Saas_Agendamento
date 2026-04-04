from flask import Blueprint, request, jsonify
from app.database import db
from app.models import Horario, Agendamento
from datetime import datetime, timedelta

# O Blueprint deve ser registrado na main com url_prefix='/admin'
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/agendamentos", methods=["GET"])
def listar_agendamentos():
    """Lista todos os agendamentos realizados para o painel"""
    try:
        # Busca agendamentos carregando o relacionamento com horário
        agendamentos = Agendamento.query.all()
        resultado = []

        for a in agendamentos:
            # Verifica se o horário existe para evitar erro de None
            data_formatada = "Sem data"
            if a.horario:
                data_formatada = a.horario.data_hora.strftime("%d/%m/%Y %H:%M")

            resultado.append(
                {
                    "id": a.id,
                    "nome": a.nome,
                    "telefone": a.telefone,
                    "data_hora": data_formatada,
                }
            )

        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/gerar-grade", methods=["POST", "OPTIONS"])
def gerar_grade_automatica():
    """
    Gera múltiplos horários de uma vez.
    Lê os dados da URL conforme o seu log: ?data=...&inicio=...&fim=...&intervalo=...
    """
    # Captura dos parâmetros da URL (Query String)
    data_alvo = request.args.get("data")  # Ex: 2026-04-03
    inicio_str = request.args.get("inicio")  # Ex: 08:00
    fim_str = request.args.get("fim")  # Ex: 18:00
    intervalo_min = int(request.args.get("intervalo", 60))

    if not all([data_alvo, inicio_str, fim_str]):
        return (
            jsonify({"erro": "Parâmetros 'data', 'inicio' e 'fim' são obrigatórios"}),
            400,
        )

    try:
        # Converte as strings para objetos datetime para cálculos
        formato = "%Y-%m-%d %H:%M"
        horario_atual = datetime.strptime(f"{data_alvo} {inicio_str}", formato)
        horario_limite = datetime.strptime(f"{data_alvo} {fim_str}", formato)

        novos_horarios = 0

        while horario_atual <= horario_limite:
            # Verifica se o horário já existe no banco para evitar erro de Unique
            existe = Horario.query.filter_by(data_hora=horario_atual).first()

            if not existe:
                novo = Horario(data_hora=horario_atual, disponivel=True)
                db.session.add(novo)
                novos_horarios += 1

            # Pula para o próximo slot (ex: +60 minutos)
            horario_atual += timedelta(minutes=intervalo_min)

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


@admin_bp.route("/horarios/limpar", methods=["DELETE"])
def limpar_horarios_vazios():
    """Remove todos os horários que não possuem agendamento"""
    try:
        # Deleta horários onde disponivel é True (sem agendamento)
        num_deletados = Horario.query.filter_by(disponivel=True).delete()
        db.session.commit()
        return jsonify({"mensagem": f"{num_deletados} horários vazios removidos."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

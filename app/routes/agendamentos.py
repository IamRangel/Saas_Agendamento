from flask import Blueprint, request, jsonify
from app.database import db
from app.models import Agendamento, Horario
from datetime import datetime

# Definindo o Blueprint que a main.py espera
agendamentos_bp = Blueprint("agendamentos", __name__)


def limpar_telefone(tel):
    """Remove caracteres não numéricos como ( ) - e espaços"""
    if not tel:
        return ""
    return "".join(filter(str.isdigit, tel))


@agendamentos_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    """Retorna a grade de horários disponíveis organizada por data"""
    try:
        # Busca apenas horários onde disponivel é True
        horarios = (
            Horario.query.filter_by(disponivel=True).order_by(Horario.data_hora).all()
        )
        grade = {}

        for h in horarios:
            data_str = h.data_hora.strftime("%Y-%m-%d")
            hora_str = h.data_hora.strftime("%H:%M")

            if data_str not in grade:
                grade[data_str] = []

            grade[data_str].append({"id": h.id, "hora": hora_str})

        return jsonify(grade), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@agendamentos_bp.route("/verificar", methods=["GET"])
def verificar_status():
    """Verifica se o cliente (via telefone) já possui um agendamento ativo"""
    telefone_bruto = request.args.get("telefone", "")
    telefone = limpar_telefone(telefone_bruto)

    if not telefone:
        return (
            jsonify({"possui_agendamento": False, "erro": "Telefone não informado"}),
            400,
        )

    # Busca o agendamento vinculado ao telefone
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
                    },
                }
            ),
            200,
        )

    return jsonify({"possui_agendamento": False}), 200


@agendamentos_bp.route("/criar", methods=["POST"])
def criar_agendamento():
    """Cria um novo agendamento e gerencia a remarcação automática"""
    nome = request.args.get("nome")
    telefone_bruto = request.args.get("telefone", "")
    horario_id = request.args.get("horario_id")

    telefone = limpar_telefone(telefone_bruto)

    if not all([nome, telefone, horario_id]):
        return jsonify({"erro": "Dados insuficientes para agendar"}), 400

    try:
        # REGRA DE NEGÓCIO: Se já existe agendamento para este ID (telefone), deleta o antigo (Remarcar)
        agendamento_antigo = Agendamento.query.filter_by(telefone=telefone).first()
        if agendamento_antigo:
            horario_antigo = Horario.query.get(agendamento_antigo.horario_id)
            if horario_antigo:
                horario_antigo.disponivel = True  # Libera o horário antigo para outros
            db.session.delete(agendamento_antigo)

        # Reserva o novo horário
        horario_novo = Horario.query.get(horario_id)
        if not horario_novo or not horario_novo.disponivel:
            return jsonify({"erro": "Este horário não está mais disponível"}), 400

        novo_agendamento = Agendamento(
            nome=nome, telefone=telefone, horario_id=horario_id
        )
        horario_novo.disponivel = False  # Marca como ocupado

        db.session.add(novo_agendamento)
        db.session.commit()

        return jsonify({"mensagem": "Agendamento confirmado com sucesso!"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno ao processar agendamento"}), 500


@agendamentos_bp.route("/cancelar", methods=["DELETE"])
def cancelar_agendamento():
    """Remove o agendamento do banco e libera o horário na grade"""
    telefone_bruto = request.args.get("telefone", "")
    telefone = limpar_telefone(telefone_bruto)

    agendamento = Agendamento.query.filter_by(telefone=telefone).first()

    if not agendamento:
        return jsonify({"erro": "Nenhum agendamento encontrado para este número"}), 404

    try:
        # Libera o horário para a grade
        horario = Horario.query.get(agendamento.horario_id)
        if horario:
            horario.disponivel = True

        db.session.delete(agendamento)
        db.session.commit()

        return (
            jsonify({"mensagem": "Agendamento cancelado. O horário está livre."}),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro ao cancelar agendamento"}), 500

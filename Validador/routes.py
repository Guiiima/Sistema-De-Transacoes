from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from rules import verificar_saldo, verificar_horario_transacao, verificar_limite_transacoes, verificar_chave_validador
from config import *
import random
import requests

validador_blueprint = Blueprint('validador', __name__)

transacoes_remetente = {
    "remetente_1": {
        "saldo": 500,
        "ultima_transacao": datetime.utcnow() - timedelta(minutes=5),
        "transacoes_recentes": 95,
        "chave_validador": "abc123"
    },

}

validador = {
    "saldo": random.uniform(30.0, 2500.0),
    "addr": 'http://' + validator_ip + ':' + str(validator_port)
}

@validador_blueprint.route('/validador/registrar', methods= ['POST'])
def register_validator():
    url = seletor_url + '/seletor'
    resp = requests.post(url= url, json= validador)

    if resp.status_code == 201:
        return resp.text

@validador_blueprint.route('/validador', methods=['POST'])
def validate_transaction():
    data = request.json

    remetente = data['remetente']
    valor_transacao = data['valor']
    taxa = data['taxa']
    horario_transacao = datetime.fromisoformat(data['horario'])
    chave_validador = data['chave_validador']


    remetente_info = transacoes_remetente.get(remetente)
    if not remetente_info:
        return jsonify({"status": 2, "message": "Remetente não encontrado"}), 400

    chave_esperada = remetente_info['chave_validador']
    saldo_remetente = remetente_info['saldo']
    horario_ultima_transacao = remetente_info['ultima_transacao']
    transacoes_recentes = remetente_info['transacoes_recentes']

    horario_atual = datetime.utcnow()


    if not verificar_saldo(saldo_remetente, valor_transacao, taxa):
        return jsonify({"status": 2, "message": "Saldo insuficiente"}), 400

    if not verificar_horario_transacao(horario_transacao, horario_atual, horario_ultima_transacao):
        return jsonify({"status": 2, "message": "Horário da transação inválido"}), 400

    if not verificar_limite_transacoes(transacoes_recentes):
        return jsonify({"status": 2, "message": "Limite de transações excedido"}), 400

    if not verificar_chave_validador(chave_validador, chave_esperada):
        return jsonify({"status": 2, "message": "Chave do validador inválida"}), 400


    transacoes_recentes += 1
    transacoes_remetente[remetente]['transacoes_recentes'] = transacoes_recentes
    transacoes_remetente[remetente]['ultima_transacao'] = horario_transacao


    return jsonify({"status": 1, "message": "Transação concluída com sucesso"}), 200

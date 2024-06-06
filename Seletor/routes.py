from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from rules import validar_seletor
import requests
import sqlite3

seletor_blueprint = Blueprint('seletor', __name__)

validadores = []
transacoes_pendentes = []

@seletor_blueprint.route('/seletor', methods=['POST'])
def register_validator():
    data = request.json

    id_validador = data['id']
    saldo = data['saldo']
    flag = data.get('flag', 0)
    addr = data['addr']

    if saldo < 50:
        return jsonify({"message": "Saldo insuficiente"}), 400

    conn = sqlite3.connect('validators.db')
    cursor = conn.cursor()

    cursor.execute("""
                    INSERT INTO validators VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   """, (id_validador, saldo, flag, 0, 0, False, 0, addr)
    )

    conn.commit()

    """
    validadores[id_validador] = {
        'saldo': saldo,
        'flag': flag,
        'flags_recebidas': 0,
        'validacoes_consecutivas': 0,
        'transacoes_coerentes': 0,
        'hold': False,
        'hold_expires': datetime.min,
        'addr': addr
    }
    """

    print(validadores)
    conn.close()
    return jsonify({"message": "Validator registered"}), 201


@seletor_blueprint.route('/seletor/teste', methods=['GET'])
def teste():
    z
    validadores1 = list(validadores.values())
    validador = validadores1[0]
    resp = requests.post(validador['addr'] + '/validador/teste', json= ping)
    print(resp.text)

    return ping + resp.text



@seletor_blueprint.route('/seletor/select', methods=['POST'])
def select_validators():
    data = request.json
    transacao = data['transacao']
    horario_atual = datetime.utcnow()

    # Verificar se há validadores suficientes
    validadores_disponiveis = {k: v for k, v in validadores.items() if not v['hold'] and v['hold_expires'] <= horario_atual}
    if len(validadores_disponiveis) < 3:
        transacoes_pendentes.append({'transacao': transacao, 'timestamp': horario_atual})
        return jsonify({"message": "Não há validadores suficientes. Transação em espera."}), 202

    # Selecionar validadores
    selecionados = validar_seletor(transacao, validadores_disponiveis)

    for id_validador in selecionados:
        validadores[id_validador]['validacoes_consecutivas'] += 1
        
    return jsonify({"selected_validators": selecionados}), 200

@seletor_blueprint.route('/seletor/consenso', methods=['POST'])
def consenso():
    data = request.json
    transacao = data['transacao']
    status = data['status']  # Lista de status dos validadores
    id_validadores = data['id_validadores']
    horario_atual = datetime.utcnow()

    aprovados = sum(1 for s in status if s == 'Aprovada')
    reprovados = len(status) - aprovados

    if aprovados > reprovados:
        resultado = 'Aprovada'
    else:
        resultado = 'Não Aprovada'

    for id_validador in id_validadores:
        validador = validadores[id_validador]
        if resultado == 'Não Aprovada' and status[id_validador] == 'Aprovada':
            validador['flags_recebidas'] += 1
            if validador['flags_recebidas'] > 2:
                del validadores[id_validador]
            else:
                validador['transacoes_coerentes'] = 0
        else:
            validador['transacoes_coerentes'] += 1
            if validador['transacoes_coerentes'] >= 10000:
                validador['flags_recebidas'] = max(0, validador['flags_recebidas'] - 1)
                validador['transacoes_coerentes'] = 0

        if validador['validacoes_consecutivas'] >= 5:
            validador['hold'] = True
            validador['hold_expires'] = horario_atual + timedelta(minutes=5)
        else:
            validador['hold'] = False
            validador['hold_expires'] = datetime.min

    return jsonify({"message": "Consenso realizado", "resultado": resultado}), 200

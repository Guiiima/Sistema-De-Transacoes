from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from rules import validar_seletor
import requests
import database
from config import *

seletor_blueprint = Blueprint('seletor', __name__)
seletor = {
    "nome": "Seletor",
    "ip": 'http://' + seletor_ip + ':' + str(seletor_port)
}

validadores = []
transacoes_pendentes = []

@seletor_blueprint.route('/seletor/registrar', methods=['POST'])
def register_seletor():
    url = banco_url + 'seletor/' + seletor["nome"] + '/' + seletor["ip"]
    print(url)
    resp = requests.post(url= url)

    return resp
    

def get_validators():
    global validadores
    texto_sql = "SELECT * FROM validators"

    validadores = database.select(texto_sql)

@seletor_blueprint.route('/seletor', methods=['POST'])
def register_validator():
    data = request.json

    saldo = data['saldo']
    addr = data['addr']

    if saldo < 50:
        return jsonify({"message": "Saldo insuficiente"}), 400
    
    database.connect('validators.db')
    texto_sql = """
        INSERT INTO validators (
            saldo, flags, validacoes, transacoes_corretas, hold, hold_expires, addr
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = [saldo, 0, 0, 0, False, 0, addr]
    
    database.execute(texto_sql, params)
    get_validators()

    database.close()

    return jsonify({"message": "Validator registered"}), 201

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

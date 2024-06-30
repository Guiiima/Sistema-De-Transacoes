from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)

# Para usar sem o docker mudar para 'localhost'
ip = 'localhost'
seletor_url = 'http://' + ip + ':5001'

validador_url = ip + ':5002'

chave_unica_global = None # id do validador

@app.route("/cadastrar_validador/", methods=['POST'])
def cadastrar_validador():
    global chave_unica_global
    dados = {'saldo': 51, 'ip': validador_url}
    resposta = requests.post(f'{seletor_url}/seletor/validador', json= dados).json()

    chave_unica_global = resposta['id']
    
    return jsonify(resposta['message']), 200

@app.route("/remover_validador/", methods=['POST'])
def remover_validador():
    resposta = requests.delete(f'/remover_validador/{chave_unica_global}')
    return resposta

@app.route("/validar_transacao/", methods=['POST'])
def validar_transacao():
    data = request.json
    
    resposta_inicial = {'message': 'Validando Transação'}
    executor.submit(processar_transacao, data)
    
    return jsonify(resposta_inicial), 200

def processar_transacao(data):
    id_transacao = data.get('id_transacao')
    ultimas_transacoes = data.get('ultimas_transacoes')
    saldo_cliente = data.get('saldo_cliente')
    valor_transacao = data.get('valor_transacao')
    horario = data.get('horario')
    horario_atual = data.get("horario_atual")
    horario_ultima_transacao = data.get("horario_ultima_transacao")
    taxa_trancacao = valor_transacao * (0.015)

    if saldo_cliente < valor_transacao + taxa_trancacao:
        dados = {'id_transacao': id_transacao, 'id_validador': chave_unica_global, 'status': 2}
        requests.post(f'{seletor_url}/transacoes/resposta', json=dados)
    
    horario_transacao = datetime.fromisoformat(horario)
    horario_atual = datetime.fromisoformat(horario_atual)
    horario_ultima_transacao = datetime.fromisoformat(horario_ultima_transacao)
    if horario_transacao > horario_atual or horario_transacao <= horario_ultima_transacao:
        dados = {'id_transacao': id_transacao, 'id_validador':chave_unica_global, 'status': 2}
        requests.post(f'{seletor_url}/transacoes/resposta', json=dados)
    
    if len(ultimas_transacoes) > 100:
        dados = {'id_transacao': id_transacao, 'id_validador': chave_unica_global, 'status': 2}
        requests.post(f'{seletor_url}/transacoes/resposta', json=dados)
    
    dados = {'id_transacao': id_transacao, 'id_validador': chave_unica_global, 'status': 1}
    requests.post(f'{seletor_url}/transacoes/resposta', json=dados)


app.run(host='0.0.0.0', port=5002, debug=True)
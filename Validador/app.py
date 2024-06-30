import uuid
from time import time
from flask import Flask, request, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
chave_unica_global = None
@app.route("/cadastrar_validador/", methods=['POST'])
def cadastro_validador():
    chave_unica = str(uuid.uuid4())
    return jsonify({"chave unica": chave_unica})
@app.route("/remover_validador/", methods=['POST'])
def remover_validador():
    resposta = requests.delete(f'/remover_validador/{chave_unica_global}')
    return resposta
@app.route('/ransacoes/resposta', methods=['POST'])
def handle_transacao_resposta():
    global chave_unica_global
    dados = request.json
    chave_unica_global = dados.get('id', None)
    resposta = requests.post('/seletor/validador',{'saldo': 51, 'ip': 'localhost:5002'})
    chave_unica_global = resposta
    return resposta.content

@app.route("/validar_transacao/", methods=['POST'])
def validar_transacao():
    data = request.json
    ultimas_transacoes = data.get('ultimas_transacoes')
    saldo_cliente = data.get('saldo_cliente')
    valor_transacao = data.get('valor_transacao')
    horario = data.get('horario')
    horario_atual = data.get("horario_atual")
    horario_ultima_transacao = data.get("horario_ultima_transacao")
    taxa_trancacao = valor_transacao * (0.015)
    if saldo_cliente < valor_transacao + taxa_trancacao:
        dados = {'id_transacao': data.get('id'), 'id_validador': chave_unica_global, 'status': 2}
        resposta = requests.post('/transacoes/resposta',  json=dados)
        return resposta.content
    horario_transacao = datetime.fromisoformat(horario)
    if horario_transacao > horario_atual or horario_transacao <= horario_ultima_transacao:
        dados = {'id_transacao': data.get('id'), 'id_validador':chave_unica_global, 'status': 2}
        resposta = requests.post('/transacoes/resposta',  json=dados)
        return resposta.content
    um_minuto_atras = horario_ultima_transacao - timedelta(minutes=-1)
    transacoes_no_ultimo_minuto = [t for t in ultimas_transacoes if datetime.fromisoformat(t['horario_ultima_transacao'])>um_minuto_atras]
    if len(transacoes_no_ultimo_minuto) > 100:
        dados = {'id_transacao': data.get('id'), 'id_validador': chave_unica_global, 'status': 2}
        resposta = requests.post('/transacoes/resposta',  json=dados)
        return resposta.content
    dados = {'id_transacao': data.get('id'), 'id_validador': chave_unica_global, 'status': 1}
    requests.post('/transacoes/resposta', json=dados)
app.run(host='0.0.0.0', port=5001, debug=True)
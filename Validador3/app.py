from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
import math

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///id.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Docker
seletor_url = 'http://seletor:5000'
validador_url = 'validador3:5000'
porta = 5000

# seletor_url = 'http://localhost:5001'
# validador_url = 'localhost:5004'
# porta = 5004


class Id(db.Model):
    id: int

    id = db.Column(db.Integer, primary_key=True)


with app.app_context():
    db.create_all()


@app.route("/cadastrar_validador/", methods=['POST'])
def cadastrar_validador():
    dados = {'saldo': 51, 'ip': validador_url}
    resposta = requests.post(f'{seletor_url}/seletor/validador', json=dados).json()

    id = Id(id=resposta['id'])
    db.session.add(id)
    db.session.commit()

    return jsonify(resposta['message']), 200


@app.route("/remover_validador/", methods=['POST'])
def remover_validador():
    id = Id.query.first()
    resposta = requests.delete(f'{seletor_url}/remover_validador/{id}')
    return resposta


@app.route("/validar_transacao/", methods=['POST'])
def validar_transacao():
    data = request.json
    resposta_inicial = {'message': 'Validando Transação'}
    id = Id.query.first()
    executor.submit(processar_transacao, data, id.id)

    return jsonify(resposta_inicial), 200


def processar_transacao(data, id):
    id_transacao = data.get('id_transacao')
    ultimas_transacoes = data.get('ultimas_transacoes')
    saldo_cliente = data.get('saldo_cliente')
    valor_transacao = data.get('valor_transacao')
    horario = data.get('horario')
    horario_atual = data.get("horario_atual")
    horario_ultima_transacao = data.get("horario_ultima_transacao")
    taxa_trancacao = math.ceil(valor_transacao * 0.015)

    if saldo_cliente < valor_transacao + taxa_trancacao:
        dados = {'id_transacao': id_transacao, 'id_validador': id, 'status': 2}
        requests.post(f'{seletor_url}/transacoes/resposta', json=dados)
        return

    horario_transacao = datetime.fromisoformat(horario)
    horario_atual = datetime.fromisoformat(horario_atual)
    horario_ultima_transacao = datetime.fromisoformat(horario_ultima_transacao)
    if horario_transacao > horario_atual or horario_transacao <= horario_ultima_transacao:
        dados = {'id_transacao': id_transacao, 'id_validador': id, 'status': 2}
        requests.post(f'{seletor_url}/transacoes/resposta', json=dados)
        return

    if len(ultimas_transacoes) > 100:
        dados = {'id_transacao': id_transacao, 'id_validador': id, 'status': 2}
        requests.post(f'{seletor_url}/transacoes/resposta', json=dados)
        return

    dados = {'id_transacao': id_transacao, 'id_validador': id, 'status': 1}
    requests.post(f'{seletor_url}/transacoes/resposta', json=dados)


app.run(host='0.0.0.0', port=porta, debug=True)

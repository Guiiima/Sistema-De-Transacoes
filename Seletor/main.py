from datetime import datetime, timedelta
import time

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
import requests
from flask import Flask, request, jsonify
import random

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///validadores.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Para usar sem o docker mudar para 'localhost'
ip = 'localhost'
banco_url = 'http://' + ip + ':5000'

seletor_url = ip + ':5001'

validacoes_pendentes = {}

@dataclass
class Validador(db.Model):
    id: int
    saldo: float
    flags: int
    validacoes: int
    transacoes_corretas: int
    hold: bool
    hold_expires: int
    ip: str

    id = db.Column(db.Integer, primary_key=True)
    saldo = db.Column(db.Float)
    flags = db.Column(db.Integer)
    validacoes = db.Column(db.Integer)
    transacoes_corretas = db.Column(db.Integer)
    hold = db.Column(db.Boolean)
    hold_expires = db.Column(db.Integer)
    ip = db.Column(db.String(30), nullable=False)


with app.app_context():
    db.create_all()

@app.route('/cadastrar_seletor', methods=['POST'])
def cadastrar_seletor():
    url = banco_url + '/seletor/Seletor/' + seletor_url
    requests.post(url)

def gerar_id():
    id = random.randint(1, 99999999)
    while (id == 0 or Validador.query.get(id) != None):
        id = random.randint(1, 99999999)

    return id

@app.route('/seletor/validador', methods=['POST'])
def cadastrar_validador():
    data = request.json

    # Verifique se todos os campos necessários estão presentes
    required_fields = ['saldo', 'ip']
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Campo {field} é obrigatório"}), 400

    # Crie uma nova instância de Validador com os dados recebidos
    # saldo tem que ser maior que 50 para poder se cadastrar
    if (data['saldo'] < 50):
        return jsonify({"status": "error", "message": "É necessário ter no mínimo 50 moedas para se tornar um validador"}), 400
    
    # tem que receber uma chave única do seletor(criar método pra gerar e devolver para salvar) - fazer no ID
    id = gerar_id()
    novo_validador = Validador(
        id=id,
        saldo=data['saldo'],
        flags=0,
        validacoes=0,
        transacoes_corretas=0,
        hold=False,
        hold_expires=0,
        ip=data['ip']
    )
    #invocar método para recuperar seu ID/Chave e então salvar

    # Adicione e confirme a nova instância no banco de dados
    try:
        db.session.add(novo_validador)
        db.session.commit()
        return jsonify({"status": "success", "message": "Validador cadastrado com sucesso", "id": id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Erro ao cadastrar validador: {str(e)}"}), 500

@app.route('/remover_validador', methods=['POST'])
def remover_validador():
    # TODO - Remoção do validador
    ...

@app.route('/transacoes/', methods=['POST'])
def validar_transacoes():
    # Escolher os validadores
    validadores = Validador.query.filter(Validador.hold == False).all()

    data = request.json
    # print(data)
    selected_validadores = []

    while len(selected_validadores) < 3:
        url = banco_url + '/cliente/' + str(data['remetente'])
        cliente = requests.get(url).json()

        # Calcular as chances de escolha com base nos percentuais
        total_saldo = sum(v.saldo for v in validadores)
        chances = []
        for validador in validadores:
            chance_base = validador.saldo / total_saldo
            if validador.flags == 1:
                chance_base *= 0.5
            elif validador.flags == 2:
                chance_base *= 0.25

            # Garantir que a chance máxima seja de 20%
            chance_final = min(chance_base, 0.2)
            chances.append(chance_final)

        # Normalizar as chances para somar 1
        total_chances = sum(chances)
        normalized_chances = [c / total_chances for c in chances]

        # Selecionar aleatoriamente os 3 validadores
        selected_validadores = random.choices(validadores, weights=normalized_chances, k=3)

        if len(selected_validadores) < 3:
            time.sleep(60)

    # Filtrar as transações pelo remetente
    url_transacoes = banco_url + '/transacoes'
    transacoes_response = requests.get(url_transacoes)
    transacoes_lista = transacoes_response.json()

    ultima_transacao = sorted(transacoes_lista, key= lambda t: t['horario']).pop()

    remetente_id = int(data['remetente'])
    transacoes_filtradas = [transacao for transacao in transacoes_lista if transacao['remetente'] == remetente_id]

    # Verificar transações com horário maior ou igual a data['horario'] - 1 minuto
    horario_limite = datetime.fromisoformat(data['horario']) - timedelta(minutes=1)
    for transacao in transacoes_filtradas:
        transacao['horario'] = datetime.strptime(transacao['horario'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%dT%H:%M:%S.%f')
    transacoes_recentes = [transacao for transacao in transacoes_filtradas if
                           datetime.fromisoformat(transacao['horario']) >= horario_limite]
    
    hora_atual = datetime.strptime(requests.get(banco_url + '/hora').json(), '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%dT%H:%M:%S.%f')

    # Exemplo de resposta (pode ser adaptado conforme necessário)
    conteudo_validacao = {
        "id_transacao": data['id'],
        "saldo_cliente": cliente['qtdMoeda'],
        "valor_transacao": data['valor'],
        "horario": data['horario'],
        "ultimas_transacoes": transacoes_recentes,
        "horario_atual": hora_atual,
        "horario_ultima_transacao": ultima_transacao['horario']
    }

    # print(conteudo_validacao)

    validadores = []
    for valid in selected_validadores:
        url = 'http://' + valid.ip + '/validar_transacao/'
        validador = { 'id': valid.id, 'status': 0 }
        validadores.append(validador)
        requests.post(url, conteudo_validacao)
    
    validacoes_pendentes[data['id']] = { validadores: validadores }
    # print(validacoes_pendentes)

    validadores_hold = Validador.query.filter(Validador.hold == False).all()
    for valid in validadores_hold:
        valid.hold_expires -= 1
        if valid.hold_expires < 1:
            valid.hold = False
        db.session.commit()

    return 200

@app.route('/transacoes/resposta', methods=['POST'])
def resposta_transacao():
    # TODO - Resposta da Transação
    # data = {id_transação, status}
    ...


app.run(host='0.0.0.0', port= 5001, debug=True)
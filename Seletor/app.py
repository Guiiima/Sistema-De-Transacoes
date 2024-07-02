from datetime import datetime, timedelta
import time
import math

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
import requests
from flask import Flask, request, jsonify
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///validadores.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Docker
banco_url = 'http://banco:5000'
seletor_url = 'seletor:5000'
porta = 5000

# banco_url = 'http://localhost:5000'
# seletor_url = 'localhost:5001'
# porta = 5001

validacoes_pendentes = {}

@dataclass
class Seletor(db.Model):
    id: int
    nome: str
    ip: str
    moedas: int

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    ip = db.Column(db.String(15), unique=False, nullable=False)
    moedas = db.Column(db.Integer, primary_key=False)


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
    active: bool
    expelled: int

    id = db.Column(db.Integer, primary_key=True)
    saldo = db.Column(db.Float)
    flags = db.Column(db.Integer)
    validacoes = db.Column(db.Integer)
    transacoes_corretas = db.Column(db.Integer)
    hold = db.Column(db.Boolean)
    hold_expires = db.Column(db.Integer)
    ip = db.Column(db.String(30), nullable=False)
    active = db.Column(db.Boolean)
    expelled = db.Column(db.Integer)


with app.app_context():
    db.create_all()


@app.route('/cadastrar_seletor', methods=['POST'])
def cadastrar_seletor():
    try:
        url = banco_url + f'/seletor/Seletor/{seletor_url}/{100}' 
        retorno = requests.post(url).json()
        print(retorno)
        seletor = Seletor(id=retorno['id'], nome=retorno['nome'], ip=retorno['ip'], moedas=retorno['moedas'])
        db.session.add(seletor)
        db.session.commit()
        return jsonify({"status": "success", "message": "Sucesso ao cadastrar seletor."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Erro ao cadastrar seletor."}), 500


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
    if data['saldo'] < 50:
        return jsonify(
            {"status": "error", "message": "É necessário ter no mínimo 50 moedas para se tornar um validador"}), 400

    controle_validador_existente = False
    validador_existente = Validador.query.filter_by(ip=data['ip']).first()
    if validador_existente is not None:
        if validador_existente.expelled > 2:
            return jsonify({"status": "error", "message": "Validador banido permanentemente"}), 400
        elif validador_existente.expelled > 0 and data['saldo'] >= 50 * 2 * validador_existente.expelled:
            atualizar_validador(validador_existente.ip, data['saldo'])
        else:
            return jsonify({"status": "error",
                            "message": f"Deve ter no mínimo {50 * 2 * validador_existente.expelled} para entrar novamente na rede"}), 400
    else:
        controle_validador_existente = True

    if controle_validador_existente:
        novo_validador = Validador(
            ip=data['ip'],
            saldo=data['saldo'],
            flags=0,
            validacoes=0,
            transacoes_corretas=0,
            hold=False,
            hold_expires=0,
            expelled=0,
            active=True
        )

        # Adicione e confirme a nova instância no banco de dados
        try:
            db.session.add(novo_validador)
            db.session.commit()
            return jsonify(
                {"status": "success", "message": "Validador cadastrado com sucesso", "id": novo_validador.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": f"Erro ao cadastrar validador: {str(e)}"}), 500


@app.route('/remover_validador/<int:id>', methods=['DELETE'])
def remover_validador():
    if (request.method == 'DELETE'):
        objeto = Validador.query.get(id)
        db.session.delete(objeto)
        db.session.commit()

        data = {
            'message': 'Validador removido com sucesso!'
        }
        return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])


@app.route('/transacoes/', methods=['POST'])
def validar_transacoes():
    data = request.json
    selected_validadores = []
    sleep = 0

    # Escolher os validadores
    validadores = (Validador.query.filter(
        Validador.hold == False,
        Validador.active == True)
                   .all())

    id_transacao = data['id']
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

        validadores_copy = validadores[:]
        normalized_chances_copy = normalized_chances[:]

        # Selecionar aleatoriamente os 3 validadores
        for _ in range(3):
            selected_validador = random.choices(validadores_copy, weights=normalized_chances_copy, k=1)[0]
            selected_validadores.append(selected_validador)

            i = validadores_copy.index(selected_validador)

            del validadores_copy[i]
            del normalized_chances_copy[i]

        if len(selected_validadores) < 3:
            if sleep > 0:
                url = banco_url + f'/transacoes/{id_transacao}/2'
                requests.post(url)
                return jsonify(['Não haviam validadores suficientes']), 500

            sleep += 1
            time.sleep(60)

    # Filtrar as transações pelo remetente
    url_transacoes = banco_url + '/transacoes'
    transacoes_response = requests.get(url_transacoes)
    transacoes_lista = transacoes_response.json()

    ultima_transacao = sorted(transacoes_lista, key=lambda t: t['horario']).pop()

    remetente_id = int(data['remetente'])
    transacoes_filtradas = [transacao for transacao in transacoes_lista if transacao['remetente'] == remetente_id]

    # Verificar transações com horário maior ou igual a data['horario'] - 1 minuto
    horario_limite = datetime.fromisoformat(data['horario']) - timedelta(minutes=1)
    for transacao in transacoes_filtradas:
        transacao['horario'] = datetime.strptime(transacao['horario'], '%a, %d %b %Y %H:%M:%S %Z').strftime(
            '%Y-%m-%dT%H:%M:%S.%f')
    transacoes_recentes = [transacao for transacao in transacoes_filtradas if
                           datetime.fromisoformat(transacao['horario']) >= horario_limite]

    hora_atual = requests.get(banco_url + '/hora').json()

    # Exemplo de resposta (pode ser adaptado conforme necessário)
    conteudo_validacao = {
        "id_transacao": id_transacao,
        "saldo_cliente": cliente['qtdMoeda'],
        "valor_transacao": data['valor'],
        "horario": data['horario'],
        "ultimas_transacoes": transacoes_recentes,
        "horario_atual": hora_atual,
        "horario_ultima_transacao": ultima_transacao['horario']
    }

    validadores = []
    validacoes_pendentes[data['id']] = {
        'transacao': {
            'remetente': data['remetente'],
            'recebedor': data['recebedor'],
            'saldo_remetente': cliente['qtdMoeda'],
            'valor': data['valor']
        },
        'validadores': validadores,
        'respostas': 0,
        'n_validadores': len(selected_validadores)
    }

    for valid in selected_validadores:
        url = 'http://' + valid.ip + '/validar_transacao/'
        validador = {'id': valid.id, 'status': 0}
        validadores.append(validador)
        requests.post(url, json=conteudo_validacao)

    validadores_hold = Validador.query.filter(Validador.hold == False).all()
    for valid in validadores_hold:
        valid.hold_expires = min((valid.hold - 1), 0)
        if valid.hold_expires < 1:
            valid.hold = False
        db.session.commit()

    return jsonify(['Transação em validação']), 200


@app.route('/transacoes/resposta', methods=['POST'])
def resposta_transacao():
    time.sleep(0.5)
    data = request.json

    id_transacao = data['id_transacao']
    id_validador = data['id_validador']
    status = data['status']

    transacao = validacoes_pendentes[id_transacao]

    validador = next((v for v in transacao['validadores'] if v['id'] == id_validador), None)

    if not validador:
        return jsonify(['Validador não selecionado']), 400

    if validador['status'] != 0:
        return jsonify(['Validador já havia respondido']), 400

    validador['status'] = status
    transacao['respostas'] += 1

    if transacao['respostas'] < transacao['n_validadores']:
        return jsonify(['Validação Recebida']), 200

    if transacao['respostas'] == transacao['n_validadores']:
        cont_status = Counter(validador['status'] for validador in transacao['validadores'])
        status_eleito, quant_status = cont_status.most_common(1)[0]

        url = banco_url + f'/transacoes/{id_transacao}/{status_eleito}'
        requests.post(url).json()

        dados_transacao = transacao['transacao']

        if status_eleito == 1:
            moedas_remetente = dados_transacao['saldo_remetente'] - math.ceil((dados_transacao['valor'] * 1.015))

            url = banco_url + f'/cliente/{str(dados_transacao['recebedor'])}'
            moedas_recebedor = requests.get(url).json()['qtdMoeda'] + dados_transacao['valor']

            editar_cliente(dados_transacao['remetente'], moedas_remetente)
            editar_cliente(dados_transacao['recebedor'], moedas_recebedor)

        validacoes_pendentes.pop(id_transacao)
        validadores_corretos = [v for v in transacao['validadores'] if v['status'] == status_eleito]
        validadores_incorretos = [v for v in transacao['validadores'] if v['status'] != status_eleito]

        if status_eleito == 1:
            taxa_validadores = math.ceil(0.01 / (len(validadores_corretos) if len(validadores_corretos) > 0 else 1))
            taxa_seletor = 0.005

            seletor = Seletor.query.first()
            seletor.moedas += math.ceil(taxa_seletor * dados_transacao['valor'])
            db.session.commit()

            seletor = Seletor.query.first()
            url = banco_url + f'/seletor/{seletor.id}/{seletor.nome}/{seletor.ip}/{seletor.moedas}'
            requests.post(url).json()

            for valid in validadores_corretos:
                validador = Validador.query.filter_by(id=valid['id']).first()
                validador.saldo = validador.saldo + (taxa_validadores * dados_transacao['valor'])
                validador.transacoes_corretas = validador.transacoes_corretas + 1
                if validador.transacoes_corretas >= 10000:
                    validador.flag = max(validador.flag - 1, 0)

                db.session.commit()

            for valid in validadores_incorretos:
                validador = Validador.query.filter_by(id=valid['id']).first()
                validador.flags = validador.flags + 1
                validador.transacoes_corretas = 0
                if validador.flags > 2:
                    validador.active = False
                    validador.expelled += 1

                db.session.commit()
        else:
            for valid in validadores_corretos:
                validador = Validador.query.filter_by(id=valid['id']).first()
                validador.transacoes_corretas = validador.transacoes_corretas + 1
                if validador.transacoes_corretas >= 10000:
                    validador.flag = max(validador.flag - 1, 0)

                db.session.commit()

            for valid in validadores_incorretos:
                validador = Validador.query.filter_by(id=valid['id']).first()
                validador.flags = validador.flags + 1
                validador.transacoes_corretas = 0
                if validador.flags > 2:
                    validador.active = False
                    validador.expelled += 1

                db.session.commit()
    else:
        return jsonify(['Validação recebida!']), 200

    return jsonify(['Validação concluída com sucesso!']), 200


def editar_cliente(id: int, moedas: int):
    url = banco_url + f'/cliente/{id}/{moedas}'
    requests.post(url)


@app.route('/validador/edit/<string:ip>/<float:saldo>', methods=['POST'])
def atualizar_validador(ip, saldo):
    if request.method == 'POST':
        try:
            data = request.json
            validador = Validador.query.filter_by(ip=ip).first()
            validador.saldo = saldo
            validador.active = True
            validador.flags = 0
            db.session.commit()
            return jsonify(['Alteração feita com sucesso'])
        except Exception as e:
            data = {
                "message": "Atualização não realizada"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])


app.run(host='0.0.0.0', port=porta, debug=True)

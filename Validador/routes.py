from flask import Blueprint, request, jsonify

validador_blueprint = Blueprint('validador', __name__)

@validador_blueprint.route('/validador', methods=['POST'])
def validate_transaction():
    data = request.json
    # Lógica para validar a transação
    return jsonify({"status": "1"})  # Exemplo de status

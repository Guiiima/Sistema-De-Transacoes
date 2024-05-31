from flask import Blueprint, request, jsonify
#from models import

banco_blueprint = Blueprint('banco', __name__)

@banco_blueprint.route('/trans', methods=['POST'])
def create_transaction():
    data = request.json
    # Lógica
    return jsonify({"message": "Transaction created"}), 201

@banco_blueprint.route('/hora', methods=['GET'])
def get_time():
    from datetime import datetime
    # Lógica
    return jsonify({"current_time": datetime.utcnow().isoformat()})

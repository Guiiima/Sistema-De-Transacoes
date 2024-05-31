from flask import Blueprint, request, jsonify

seletor_blueprint = Blueprint('seletor', __name__)

@seletor_blueprint.route('/seletor', methods=['POST'])
def register_validator():
    data = request.json
    # Lógica
    return jsonify({"message": "Validator registered"}), 201

@seletor_blueprint.route('/seletor/select', methods=['POST'])
def select_validators():
    data = request.json
    # Lógica
    return jsonify({"selected_validators"})

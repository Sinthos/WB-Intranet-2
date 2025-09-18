from flask import Blueprint, jsonify, request
from database import get_car_by_id, update_car, delete_car

bp = Blueprint('car', __name__)


@bp.route('/car/<int:car_id>', methods=['GET'])
def get_car(car_id):
    car = get_car_by_id(car_id)

    if car:
        # Convert Row object to dictionary
        car_dict = dict(car)
        return jsonify(car_dict)
    else:
        return jsonify({'error': 'Fahrzeug nicht gefunden'}), 404


@bp.route('/car/<int:car_id>', methods=['PUT'])
def update_car_route(car_id):
    if not request.is_json:
        return jsonify({'error': 'Content-Type muss application/json sein'}), 400

    try:
        data = request.get_json()
        update_car(car_id, data)
        return jsonify({'message': 'Fahrzeug erfolgreich aktualisiert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/car/<int:car_id>', methods=['DELETE'])
def delete_car_route(car_id):
    try:
        delete_car(car_id)
        return jsonify({'message': 'Fahrzeug erfolgreich gelöscht'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
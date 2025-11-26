from flask import Blueprint, jsonify, request
from database import get_car_by_id, update_car, delete_car
from models import db, Car
from sqlalchemy import func, desc
from datetime import datetime, timedelta

bp = Blueprint('car', __name__)


@bp.route('/car/<int:car_id>', methods=['GET'])
def get_car(car_id):
    car = get_car_by_id(car_id)

    if car:
        # Convert Car object to dictionary
        return jsonify(car.to_dict())
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


# ============== Dashboard API-Endpunkte ==============

@bp.route('/api/cars/stats', methods=['GET'])
def get_car_stats():
    """Gibt Statistiken über alle Fahrzeuge zurück."""
    try:
        # Gesamtanzahl
        total = Car.query.count()
        
        # Durchschnittspreis
        avg_price_result = db.session.query(func.avg(Car.price)).scalar()
        avg_price = float(avg_price_result) if avg_price_result else 0
        
        # Durchschnittliche Kilometer
        avg_mileage_result = db.session.query(func.avg(Car.mileage)).scalar()
        avg_mileage = float(avg_mileage_result) if avg_mileage_result else 0
        
        # Fahrzeuge diese Woche hinzugefügt
        week_ago = datetime.now() - timedelta(days=7)
        recent_count = Car.query.filter(Car.created_at >= week_ago).count()
        
        # Fahrzeuge nach Marke (Top 5)
        brands = db.session.query(
            Car.brand, 
            func.count(Car.id).label('count')
        ).group_by(Car.brand).order_by(desc('count')).limit(5).all()
        
        brands_data = [{'brand': b[0], 'count': b[1]} for b in brands]
        
        # Fahrzeuge nach Kraftstoff
        fuel_types = db.session.query(
            Car.fuel_type,
            func.count(Car.id).label('count')
        ).group_by(Car.fuel_type).all()
        
        fuel_data = [{'fuel_type': f[0], 'count': f[1]} for f in fuel_types]
        
        return jsonify({
            'total': total,
            'avg_price': round(avg_price, 2),
            'avg_mileage': round(avg_mileage, 2),
            'recent_count': recent_count,
            'brands': brands_data,
            'fuel_types': fuel_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/cars/recent', methods=['GET'])
def get_recent_cars():
    """Gibt die zuletzt hinzugefügten Fahrzeuge zurück."""
    try:
        limit = request.args.get('limit', 5, type=int)
        limit = min(limit, 20)  # Maximal 20 Fahrzeuge
        
        cars = Car.query.order_by(desc(Car.created_at)).limit(limit).all()
        
        result = []
        for car in cars:
            result.append({
                'id': car.id,
                'listing_number': car.listing_number,
                'brand': car.brand,
                'model': car.model,
                'price': car.price,
                'mileage': car.mileage,
                'created_at': car.created_at.strftime('%d.%m.%Y') if car.created_at else ''
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/cars/export', methods=['GET'])
def export_cars():
    """Exportiert alle Fahrzeuge als JSON (für CSV-Export im Frontend)."""
    try:
        cars = Car.query.order_by(desc(Car.created_at)).all()
        
        result = []
        for car in cars:
            result.append({
                'id': car.id,
                'listing_number': car.listing_number,
                'brand': car.brand,
                'model': car.model,
                'engine_capacity': car.engine_capacity,
                'power': car.power,
                'fuel_type': car.fuel_type,
                'transmission': car.transmission,
                'mileage': car.mileage,
                'first_registration': car.first_registration,
                'features': car.features,
                'eco_badge': car.eco_badge,
                'price': car.price,
                'vat_deductible': car.vat_deductible,
                'seller': car.seller,
                'created_at': car.created_at.strftime('%d.%m.%Y %H:%M') if car.created_at else ''
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

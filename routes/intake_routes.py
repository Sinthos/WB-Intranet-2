"""
Routes für das Fahrzeug-Aufnahmeblatt (Vehicle Intake Form)
Enthält CRUD-Operationen und PDF-Export
"""
from flask import Blueprint, jsonify, request, render_template, make_response
from models import db, VehicleIntake
from sqlalchemy import desc
from datetime import datetime
import json

bp = Blueprint('intake', __name__)


# ============== API-Endpunkte ==============

@bp.route('/api/intake', methods=['POST'])
def create_intake():
    """Erstellt ein neues Aufnahmeblatt."""
    if not request.is_json:
        return jsonify({'error': 'Content-Type muss application/json sein'}), 400
    
    try:
        data = request.get_json()
        
        # Pflichtfelder prüfen
        if not data.get('brand'):
            return jsonify({'error': 'Marke ist erforderlich'}), 400
        if not data.get('model_variant'):
            return jsonify({'error': 'Modell/Variante ist erforderlich'}), 400
        
        # Neues Aufnahmeblatt erstellen
        intake = VehicleIntake()
        intake.from_dict(data)
        
        db.session.add(intake)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aufnahmeblatt erfolgreich erstellt',
            'id': intake.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/intake/<int:intake_id>', methods=['GET'])
def get_intake(intake_id):
    """Gibt ein einzelnes Aufnahmeblatt zurück."""
    intake = VehicleIntake.query.get(intake_id)
    
    if not intake:
        return jsonify({'error': 'Aufnahmeblatt nicht gefunden'}), 404
    
    return jsonify(intake.to_dict())


@bp.route('/api/intake/<int:intake_id>', methods=['PUT'])
def update_intake(intake_id):
    """Aktualisiert ein bestehendes Aufnahmeblatt."""
    if not request.is_json:
        return jsonify({'error': 'Content-Type muss application/json sein'}), 400
    
    intake = VehicleIntake.query.get(intake_id)
    if not intake:
        return jsonify({'error': 'Aufnahmeblatt nicht gefunden'}), 404
    
    try:
        data = request.get_json()
        intake.from_dict(data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aufnahmeblatt erfolgreich aktualisiert'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/intake/<int:intake_id>', methods=['DELETE'])
def delete_intake(intake_id):
    """Löscht ein Aufnahmeblatt."""
    intake = VehicleIntake.query.get(intake_id)
    if not intake:
        return jsonify({'error': 'Aufnahmeblatt nicht gefunden'}), 404
    
    try:
        db.session.delete(intake)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aufnahmeblatt erfolgreich gelöscht'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/intakes', methods=['GET'])
def list_intakes():
    """Gibt alle Aufnahmeblätter zurück (mit Pagination)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Maximal 100 pro Seite
        
        # Sortierung
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Query aufbauen
        query = VehicleIntake.query
        
        # Suchfilter
        search = request.args.get('search', '')
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                db.or_(
                    VehicleIntake.brand.ilike(search_filter),
                    VehicleIntake.model_variant.ilike(search_filter),
                    VehicleIntake.vin.ilike(search_filter),
                    VehicleIntake.internal_number.ilike(search_filter)
                )
            )
        
        # Sortierung anwenden
        if hasattr(VehicleIntake, sort_by):
            order_column = getattr(VehicleIntake, sort_by)
            if sort_order == 'desc':
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
        else:
            query = query.order_by(desc(VehicleIntake.created_at))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        result = {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/intake/options', methods=['GET'])
def get_intake_options():
    """Gibt alle verfügbaren Optionen für Dropdown-Felder zurück."""
    return jsonify({
        'fuel_types': VehicleIntake.get_fuel_type_options(),
        'exterior_colors': VehicleIntake.get_exterior_color_options(),
        'exterior_features': VehicleIntake.get_exterior_feature_options(),
        'interior_colors': VehicleIntake.get_interior_color_options(),
        'interior_materials': VehicleIntake.get_interior_material_options(),
        'comfort_features': VehicleIntake.get_comfort_feature_options(),
        'infotainment_features': VehicleIntake.get_infotainment_feature_options(),
        'safety_features': VehicleIntake.get_safety_feature_options(),
        'airbags': VehicleIntake.get_airbag_options(),
        'climate_options': VehicleIntake.get_climate_options(),
        'parking_features': VehicleIntake.get_parking_feature_options(),
        'drive_types': VehicleIntake.get_drive_type_options(),
        'transmissions': VehicleIntake.get_transmission_options(),
        'emission_classes': VehicleIntake.get_emission_class_options(),
        'service_book_options': VehicleIntake.get_service_book_options(),
        'accident_damage_options': VehicleIntake.get_accident_damage_options(),
        'warranty_options': VehicleIntake.get_warranty_options()
    })


@bp.route('/api/intake/<int:intake_id>/pdf', methods=['GET'])
def get_intake_pdf(intake_id):
    """Generiert eine druckbare PDF-Ansicht des Aufnahmeblatts."""
    intake = VehicleIntake.query.get(intake_id)
    
    if not intake:
        return jsonify({'error': 'Aufnahmeblatt nicht gefunden'}), 404
    
    # Daten für Template vorbereiten
    data = intake.to_dict()
    
    # Eco-Badge Farbe bestimmen
    eco_badge_colors = {
        'grün': ('#22c55e', '#16a34a'),
        'gelb': ('#eab308', '#ca8a04'),
        'rot': ('#ef4444', '#dc2626'),
    }
    eco_badge = data.get('eco_badge', 'grün')
    eco_color, eco_stroke = eco_badge_colors.get(eco_badge, ('#22c55e', '#16a34a'))
    
    return render_template(
        'intake_pdf.html',
        intake=data,
        eco_badge_color=eco_color,
        eco_badge_stroke=eco_stroke,
        print_date=datetime.now().strftime('%d.%m.%Y')
    )


@bp.route('/api/intake/generate-number', methods=['GET'])
def generate_internal_number():
    """Generiert eine neue interne Fahrzeugnummer."""
    try:
        year = datetime.now().year
        
        # Zähle bestehende Einträge dieses Jahres
        count = VehicleIntake.query.filter(
            VehicleIntake.internal_number.like(f'{year}-%')
        ).count()
        
        # Neue Nummer generieren
        new_number = f'{year}-{str(count + 1).zfill(3)}'
        
        return jsonify({
            'internal_number': new_number
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== View-Endpunkte ==============

@bp.route('/intake/new')
def new_intake_form():
    """Zeigt das Formular für ein neues Aufnahmeblatt."""
    return render_template('intake_form.html', intake=None, mode='new')


@bp.route('/intake/<int:intake_id>/edit')
def edit_intake_form(intake_id):
    """Zeigt das Formular zum Bearbeiten eines Aufnahmeblatts."""
    intake = VehicleIntake.query.get(intake_id)
    if not intake:
        return render_template('404.html'), 404
    
    return render_template('intake_form.html', intake=intake.to_dict(), mode='edit')


@bp.route('/intake/<int:intake_id>/view')
def view_intake(intake_id):
    """Zeigt ein Aufnahmeblatt in der Druckansicht."""
    intake = VehicleIntake.query.get(intake_id)
    if not intake:
        return render_template('404.html'), 404
    
    data = intake.to_dict()
    
    # Eco-Badge Farbe bestimmen
    eco_badge_colors = {
        'grün': ('#22c55e', '#16a34a'),
        'gelb': ('#eab308', '#ca8a04'),
        'rot': ('#ef4444', '#dc2626'),
    }
    eco_badge = data.get('eco_badge', 'grün')
    eco_color, eco_stroke = eco_badge_colors.get(eco_badge, ('#22c55e', '#16a34a'))
    
    return render_template(
        'intake_pdf.html',
        intake=data,
        eco_badge_color=eco_color,
        eco_badge_stroke=eco_stroke,
        print_date=datetime.now().strftime('%d.%m.%Y')
    )


@bp.route('/intakes')
def list_intakes_view():
    """Zeigt die Übersicht aller Aufnahmeblätter."""
    return render_template('intake_list.html')

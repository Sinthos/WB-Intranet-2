from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from weasyprint import HTML
from io import BytesIO
from database import get_all_cars, get_car_by_id, insert_car
import os

bp = Blueprint('views', __name__)


def get_eco_badge_colors(badge_number):
    colors = {
        1: ('#000000', '#000000'),  # Black
        2: ('#e4002b', '#b30022'),  # Red
        3: ('#ffd700', '#b39700'),  # Yellow
        4: ('#3fa240', '#2d7500'),  # Green
        5: ('#0000ff', '#000099')  # Blue
    }
    return colors.get(badge_number, colors[4])


@bp.route('/static/images/<path:filename>')
def serve_image(filename):
    """Serve images for PDF generation"""
    static_dir = os.path.join(current_app.root_path, 'static', 'images')
    return send_file(os.path.join(static_dir, filename))


@bp.route('/view-cars')
def view_cars():
    search_term = request.args.get('search', '')
    sort_by = request.args.get('sort', 'id')
    sort_order = request.args.get('order', 'asc')

    cars = get_all_cars(search_term, sort_by, sort_order)

    return render_template('view_cars.html',
                           cars=cars,
                           search_term=search_term,
                           sort_by=sort_by,
                           sort_order=sort_order)


def generate_pdf_from_template(html_content):
    """Helper function to generate PDF with correct image handling"""
    pdf_file = BytesIO()

    # Get the absolute path to the static directory
    static_dir = os.path.join(current_app.root_path, 'static')

    # Create HTML object with base URL
    html = HTML(
        string=html_content,
        base_url=request.url_root
    )

    # Generate PDF
    html.write_pdf(
        pdf_file,
        presentational_hints=True
    )

    pdf_file.seek(0)
    return pdf_file


@bp.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """Generate PDF for a new car and save to database"""
    car_data = {
        'listing_number': request.form.get('listing_number', ''),
        'brand': request.form.get('brand', ''),
        'model': request.form.get('model', ''),
        'engine_capacity': int(request.form.get('engine_capacity', 0)),
        'power': int(request.form.get('power', 0)),
        'fuel_type': request.form.get('fuel_type', ''),
        'transmission': request.form.get('transmission', ''),
        'mileage': int(request.form.get('mileage', 0)),
        'first_registration': request.form.get('first_registration', ''),
        'features': [feature.strip() for feature in request.form.get('features', '').split('\n') if feature.strip()],
        'eco_badge': int(request.form.get('eco_badge', 4)),
        'price': int(request.form.get('price', 0)),
        'vat_deductible': bool(request.form.get('vat_deductible', False))
    }

    # Speichern in der Datenbank
    try:
        insert_car(car_data)
    except Exception as e:
        current_app.logger.error(f"Fehler beim Speichern des Fahrzeugs: {str(e)}")
        return jsonify({'error': 'Fehler beim Speichern des Fahrzeugs'}), 500

    # Get eco badge colors
    eco_badge_color, eco_badge_stroke = get_eco_badge_colors(car_data['eco_badge'])

    # Generate PDF
    html_content = render_template('car_template.html',
                               car=car_data,
                               eco_badge_color=eco_badge_color,
                               eco_badge_stroke=eco_badge_stroke)

    pdf_file = generate_pdf_from_template(html_content)

    filename = f"{car_data['brand']}_{car_data['model']}_{car_data['listing_number']}.pdf"
    filename = filename.replace(" ", "_")

    return send_file(
        pdf_file,
        download_name=filename,
        as_attachment=True,
        mimetype='application/pdf'
    )


@bp.route('/car/<int:car_id>/pdf')
def generate_car_pdf(car_id):
    """Generate PDF for an existing car"""
    car = get_car_by_id(car_id)

    if not car:
        return jsonify({'error': 'Fahrzeug nicht gefunden'}), 404

    # Convert Row object to dictionary
    car_dict = dict(car)

    # Convert features string back to list
    car_dict['features'] = car_dict['features'].split(', ')

    # Get eco badge colors
    eco_badge_color, eco_badge_stroke = get_eco_badge_colors(car_dict['eco_badge'])

    # Generate PDF
    html_content = render_template('car_template.html',
                                   car=car_dict,
                                   eco_badge_color=eco_badge_color,
                                   eco_badge_stroke=eco_badge_stroke)

    pdf_file = generate_pdf_from_template(html_content)

    filename = f"{car_dict['brand']}_{car_dict['model']}_{car_dict['listing_number']}.pdf"
    filename = filename.replace(" ", "_")

    return send_file(
        pdf_file,
        download_name=filename,
        as_attachment=True,
        mimetype='application/pdf'
    )
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, redirect, url_for
from weasyprint import HTML
from io import BytesIO
from database import get_all_cars, get_car_by_id, insert_car
from forms import CarForm
import os

bp = Blueprint('views', __name__)


def get_eco_badge_colors(badge_number):
    colors = {
        1: ('#000000', '#000000'),  # Black
        2: ('#e4002b', '#b30022'),  # Red
        3: ('#ffd700', '#b39700'),  # Yellow
        4: ('#3fa240', '#2d7500'),  # Green
        5: ('#0000ff', '#000099')   # Blue
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
    html = HTML(string=html_content, base_url=request.url_root)
    html.write_pdf(pdf_file, presentational_hints=True)
    pdf_file.seek(0)
    return pdf_file


@bp.route('/car-form', methods=['GET', 'POST'])
def car_form():
    """Handle car creation form and PDF generation."""
    form = CarForm()
    if form.validate_on_submit():
        car_data = {
            'listing_number': form.listing_number.data,
            'brand': form.brand.data,
            'model': form.model.data,
            'engine_capacity': form.engine_capacity.data,
            'power': form.power.data,
            'fuel_type': form.fuel_type.data,
            'transmission': form.transmission.data,
            'mileage': form.mileage.data,
            'first_registration': form.first_registration.data,
            'features': [feature.strip() for feature in form.features.data.splitlines() if feature.strip()],
            'eco_badge': form.eco_badge.data,
            'price': form.price.data,
            'vat_deductible': form.vat_deductible.data,
            'seller': form.seller.data
        }

        try:
            new_car_id = insert_car(car_data)
            # Redirect to the PDF generation route for the new car
            return redirect(url_for('views.generate_car_pdf', car_id=new_car_id))
        except Exception as e:
            current_app.logger.error(f"Error saving car: {str(e)}")
            # In a real app, you might want to flash a message to the user
            return render_template('500.html', error="Error saving car"), 500

    return render_template('car_form.html', form=form)


@bp.route('/car/<int:car_id>/pdf')
def generate_car_pdf(car_id):
    """Generate PDF for an existing car"""
    car = get_car_by_id(car_id)
    if not car:
        return render_template('404.html'), 404

    car_dict = car.to_dict()
    car_dict['features'] = car_dict['features'].split(', ')

    eco_badge_color, eco_badge_stroke = get_eco_badge_colors(car_dict['eco_badge'])
    html_content = render_template('car_template.html',
                                   car=car_dict,
                                   eco_badge_color=eco_badge_color,
                                   eco_badge_stroke=eco_badge_stroke,
                                   seller=car_dict.get('seller', 'Auto Berndl'))
    pdf_file = generate_pdf_from_template(html_content)
    filename = f"{car_dict['brand']}_{car_dict['model']}_{car_dict['listing_number']}.pdf".replace(" ", "_")

    return send_file(
        pdf_file,
        download_name=filename,
        as_attachment=True,
        mimetype='application/pdf'
    )

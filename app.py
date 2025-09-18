# app.py
from flask import Flask, render_template, send_from_directory
import os
from database import init_db
from routes import car_routes, view_routes

app = Flask(__name__)

# Konfiguration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size
app.secret_key = os.getenv('SECRET_KEY', 'dev')  # Setze einen Secret Key für Sessions
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')

# Stelle sicher, dass Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(car_routes.bp)
app.register_blueprint(view_routes.bp)

# Initialize database
init_db()

@app.template_filter('numberformat')
def numberformat_filter(value):
    """Template Filter für Zahlenformatierung"""
    try:
        return "{:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Route für statische Dateien"""
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    """Homepage Route"""
    return render_template('home.html')

@app.route('/car-form')
def car_form():
    """Formular für neue Fahrzeuge"""
    return render_template('car_form.html')

@app.route('/intake-form')
def intake_form():
    """Aufnahmeblatt Route"""
    return render_template('intake_form.html')

@app.errorhandler(404)
def not_found_error(error):
    """404 Fehlerseite"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 Fehlerseite"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
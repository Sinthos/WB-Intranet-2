# app.py
from flask import Flask, render_template, send_from_directory, jsonify, request
import os
import subprocess
import shutil
from datetime import datetime
from models import db, Car
from routes import car_routes, view_routes
from version_utils import get_full_version_info, check_for_updates, get_changelog

app = Flask(__name__)

# Konfiguration
# Stelle sicher, dass das data-Verzeichnis existiert
data_dir = os.path.join(app.root_path, 'data')
os.makedirs(data_dir, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size
app.secret_key = os.getenv('SECRET_KEY', 'dev')  # Setze einen Secret Key für Sessions
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(data_dir, "car_data.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Stelle sicher, dass Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(car_routes.bp)
app.register_blueprint(view_routes.bp)

# Initialize DB
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Migration: Füge in_stock Spalte hinzu, falls sie nicht existiert
    # und setze Standardwert für bestehende Einträge
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('cars')]
        
        if 'in_stock' not in columns:
            # Spalte existiert nicht - füge sie hinzu
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE cars ADD COLUMN in_stock BOOLEAN DEFAULT 1 NOT NULL'))
                conn.commit()
            print("Migration: in_stock Spalte hinzugefügt")
        else:
            # Spalte existiert - setze NULL-Werte auf 1 (im Bestand)
            with db.engine.connect() as conn:
                conn.execute(text('UPDATE cars SET in_stock = 1 WHERE in_stock IS NULL'))
                conn.commit()
    except Exception as e:
        print(f"Migration-Hinweis: {e}")

@app.template_filter('numberformat')
def numberformat_filter(value):
    """Template Filter für Zahlenformatierung"""
    try:
        return "{:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value


@app.context_processor
def inject_version():
    """Injiziert Versionsinformationen in alle Templates."""
    return {'version_info': get_full_version_info()}


@app.context_processor
def inject_now():
    """Injiziert die now() Funktion in alle Templates."""
    return {'now': datetime.now}

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Route für statische Dateien"""
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    """Homepage Route"""
    return render_template('home.html')


@app.route('/intake-form')
def intake_form():
    """Aufnahmeblatt Route"""
    return render_template('intake_form.html')


# ============== API-Endpunkte für Versionierung ==============

@app.route('/api/version')
def api_version():
    """Gibt die aktuelle Version zurück."""
    return jsonify(get_full_version_info())


@app.route('/api/check-update')
def api_check_update():
    """Prüft auf verfügbare Updates."""
    return jsonify(check_for_updates())


@app.route('/api/changelog')
def api_changelog():
    """Gibt die letzten Commits als Changelog zurück."""
    limit = request.args.get('limit', 10, type=int)
    return jsonify(get_changelog(limit=limit))


def _get_bash_executable() -> str:
    """Findet den Pfad zur Bash-Executable."""
    # Versuche bash im PATH zu finden
    bash_path = shutil.which('bash')
    if bash_path:
        return bash_path
    
    # Fallback: Bekannte Pfade prüfen (macOS/Linux)
    common_paths = [
        '/bin/bash',
        '/usr/bin/bash',
        '/usr/local/bin/bash',
        '/opt/homebrew/bin/bash',
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    return 'bash'  # Fallback


@app.route('/api/update', methods=['POST'])
def api_update():
    """
    Führt ein Update durch (von localhost und lokalem Netzwerk erlaubt).
    Startet das update.sh Skript.
    """
    # Sicherheitscheck: Localhost und lokales Netzwerk erlauben
    remote_addr = request.remote_addr
    allowed = False
    
    # Localhost erlauben
    if remote_addr in ['127.0.0.1', '::1', 'localhost']:
        allowed = True
    # Private Netzwerke erlauben (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
    elif remote_addr.startswith('192.168.') or remote_addr.startswith('10.'):
        allowed = True
    elif remote_addr.startswith('172.'):
        # 172.16.0.0 - 172.31.255.255
        try:
            second_octet = int(remote_addr.split('.')[1])
            if 16 <= second_octet <= 31:
                allowed = True
        except (ValueError, IndexError):
            pass
    
    if not allowed:
        return jsonify({
            'success': False,
            'error': 'Update nur von localhost oder lokalem Netzwerk erlaubt'
        }), 403
    
    try:
        # Pfad zum Update-Skript
        update_script = os.path.join(app.root_path, 'update.sh')
        
        if not os.path.exists(update_script):
            return jsonify({
                'success': False,
                'error': 'Update-Skript nicht gefunden'
            }), 404
        
        # Finde bash executable
        bash_exe = _get_bash_executable()
        
        # Prüfe ob bash gefunden wurde
        if not os.path.isfile(bash_exe):
            return jsonify({
                'success': False,
                'error': f'Bash nicht gefunden. Bitte manuell ausführen: bash update.sh'
            }), 500
        
        # Starte Update-Skript im Hintergrund
        subprocess.Popen(
            [bash_exe, update_script],
            cwd=app.root_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Update gestartet. Die Anwendung wird in Kürze neu gestartet.'
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': f'Bash nicht gefunden. Bitte manuell ausführen: bash update.sh'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/settings')
def settings():
    """Einstellungsseite mit Update-Funktion."""
    version_info = get_full_version_info()
    # Update-Check wird NICHT automatisch durchgeführt - nur manuell über Button
    # Dies verhindert GitHub API Rate-Limiting
    update_info = {
        "update_available": False,
        "current_version": version_info.get("version", "0.0.0"),
        "current_commit": version_info.get("commit_full", ""),
        "latest_commit": None,
        "latest_commit_date": None,
        "latest_commit_message": None,
        "error": None,
        "checked": False  # Zeigt an, dass noch nicht geprüft wurde
    }
    # Changelog wird über lokales Git geladen (kein API-Aufruf)
    changelog = get_changelog(limit=10)
    return render_template('settings.html', 
                         version_info=version_info,
                         update_info=update_info,
                         changelog=changelog)

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

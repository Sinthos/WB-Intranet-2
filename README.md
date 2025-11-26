# WB-Intranet 2 - Auto Berndl Intranet

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)

Internes Verwaltungssystem für Fahrzeugauszeichnungen und Aufnahmeblätter.

## 🚀 Features

- **Fahrzeugauszeichnung**: Erstellen Sie professionelle PDF-Auszeichnungen für Fahrzeuge
- **Aufnahmeblatt**: Digitales Erfassen von Fahrzeugdaten
- **Fahrzeugübersicht**: Durchsuchbare Liste aller Fahrzeuge mit Export-Funktion
- **Dashboard**: Statistiken und Schnellzugriff auf wichtige Funktionen
- **Dark Mode**: Augenfreundliches Design für jede Tageszeit
- **Responsive Design**: Optimiert für Desktop und breite Monitore
- **Auto-Update**: Einfache Updates direkt aus der Anwendung

---

## 📦 Installation

### 1-Klick-Installation (Empfohlen für Proxmox LXC)

Führen Sie folgenden Befehl in einem **Debian/Ubuntu LXC Container** aus:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Sinthos/WB-Intranet-2/main/install.sh)
```

Oder mit wget:

```bash
wget -qO- https://raw.githubusercontent.com/Sinthos/WB-Intranet-2/main/install.sh | bash
```

Das Skript:
- ✅ Installiert Python 3.9+ und alle Abhängigkeiten
- ✅ Klont das Repository
- ✅ Erstellt eine virtuelle Python-Umgebung
- ✅ Startet die Anwendung
- ✅ Erstellt einen Systemd-Service für Auto-Start

### Manuelle Installation

#### Voraussetzungen

- Python 3.9 oder höher
- Git
- pip

#### Schritte

```bash
# Repository klonen
git clone https://github.com/Sinthos/WB-Intranet-2.git
cd WB-Intranet-2

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python app.py
```

#### System-Abhängigkeiten (Debian/Ubuntu)

Für die PDF-Generierung werden folgende Pakete benötigt:

```bash
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

---

## 🔄 Updates

### Über die Web-Oberfläche

1. Öffnen Sie **Einstellungen** (Zahnrad-Symbol)
2. Klicken Sie auf **Update installieren** (wenn verfügbar)
3. Die Anwendung startet automatisch neu

### Über die Kommandozeile

```bash
cd /opt/wb-intranet  # oder Ihr Installationsverzeichnis
bash update.sh
```

### Update-Optionen

```bash
# Normales Update
bash update.sh

# Nur Backup erstellen
bash update.sh -b

# Update ohne Bestätigung
bash update.sh -f

# Update ohne Backup
bash update.sh --no-backup

# Hilfe anzeigen
bash update.sh -h
```

### Manuelles Update

Falls das Update-Skript nicht funktioniert:

```bash
cd /opt/wb-intranet

# Änderungen von GitHub holen
git pull origin main

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Abhängigkeiten aktualisieren
pip install -r requirements.txt

# Service neu starten
sudo systemctl restart wb-intranet
```

---

## 🖥️ Zugriff

Nach der Installation ist die Anwendung erreichbar unter:

- **Lokal**: http://localhost:5000
- **Im Netzwerk**: http://[IP-ADRESSE]:5000

---

## ⌨️ Tastenkürzel

| Kürzel | Aktion |
|--------|--------|
| `Ctrl+Shift+N` | Neues Fahrzeug anlegen |
| `Ctrl+Shift+L` | Fahrzeugübersicht öffnen |
| `Ctrl+Shift+H` | Zur Startseite |
| `Esc` | Modal schließen |

---

## 📁 Projektstruktur

```
WB-Intranet-2/
├── app.py                 # Flask-Hauptanwendung
├── database.py            # Datenbankfunktionen
├── models.py              # SQLAlchemy-Modelle
├── forms.py               # WTForms-Formulare
├── version_utils.py       # Versionsverwaltung
├── requirements.txt       # Python-Abhängigkeiten
├── install.sh             # Installationsskript
├── update.sh              # Update-Skript
├── VERSION                # Versionsnummer
├── routes/
│   ├── car_routes.py      # API-Routen für Fahrzeuge
│   └── view_routes.py     # View-Routen
├── templates/
│   ├── base.html          # Basis-Template
│   ├── home.html          # Startseite/Dashboard
│   ├── car_form.html      # Fahrzeugformular
│   ├── view_cars.html     # Fahrzeugübersicht
│   ├── settings.html      # Einstellungen
│   └── ...
├── static/
│   ├── images/            # Bilder und Logos
│   └── js/                # JavaScript-Dateien
├── data/
│   └── car_data.db        # SQLite-Datenbank
├── backups/               # Datenbank-Backups
└── venv/                  # Virtuelle Python-Umgebung
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `PORT` | Server-Port | `5000` |
| `SECRET_KEY` | Flask Secret Key | `dev` |
| `DATABASE_URL` | Datenbank-URL | `sqlite:///data/car_data.db` |
| `FLASK_ENV` | Umgebung | `production` |

### Systemd Service anpassen

Der Service befindet sich unter `/etc/systemd/system/wb-intranet.service`:

```ini
[Unit]
Description=WB-Intranet 2 - Auto Berndl Intranet
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wb-intranet
Environment="PATH=/opt/wb-intranet/venv/bin"
ExecStart=/opt/wb-intranet/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Nach Änderungen:
```bash
sudo systemctl daemon-reload
sudo systemctl restart wb-intranet
```

---

## 💾 Backup & Restore

### Backup erstellen

```bash
# Über das Update-Skript
bash update.sh -b

# Manuell
cp data/car_data.db backups/car_data_$(date +%Y%m%d).db
```

### Backup wiederherstellen

```bash
# Service stoppen
sudo systemctl stop wb-intranet

# Backup wiederherstellen
cp backups/car_data_DATUM.db data/car_data.db

# Service starten
sudo systemctl start wb-intranet
```

---

## 🐛 Fehlerbehebung

### Service startet nicht

```bash
# Status prüfen
sudo systemctl status wb-intranet

# Logs prüfen
sudo journalctl -u wb-intranet -f

# Service manuell starten zum Debuggen
cd /opt/wb-intranet
source venv/bin/activate
python app.py
```

### Datenbank-Fehler

```bash
# Datenbank-Berechtigungen prüfen
chmod 755 data/
chmod 644 data/car_data.db
```

### Port bereits belegt

```bash
# Prüfen welcher Prozess den Port verwendet
sudo lsof -i :5000

# Anderen Port verwenden (in app.py oder via Umgebungsvariable)
PORT=8080 python app.py
```

### PDF-Generierung funktioniert nicht

```bash
# Fehlende Abhängigkeiten installieren
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info
```

---

## 📝 API-Endpunkte

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/version` | Aktuelle Version |
| GET | `/api/check-update` | Auf Updates prüfen |
| GET | `/api/changelog` | Changelog abrufen |
| POST | `/api/update` | Update starten (nur lokales Netzwerk) |
| GET | `/api/cars/stats` | Fahrzeugstatistiken |
| GET | `/api/cars/recent` | Letzte Fahrzeuge |
| GET | `/api/cars/export` | Alle Fahrzeuge exportieren |
| GET | `/car/<id>` | Fahrzeug abrufen |
| PUT | `/car/<id>` | Fahrzeug aktualisieren |
| DELETE | `/car/<id>` | Fahrzeug löschen |

---

## 🤝 Beitragen

1. Fork erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

---

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

---

## 📞 Support

Bei Fragen oder Problemen:
- [GitHub Issues](https://github.com/Sinthos/WB-Intranet-2/issues)

---

**Made with ❤️ for Auto Berndl**

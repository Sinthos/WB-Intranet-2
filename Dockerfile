# Dockerfile
FROM python:3.9-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten für WeasyPrint und andere Pakete installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt
COPY requirements.txt .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Code
COPY . .

# Erstelle Ordner für die Datenbank und statische Dateien
RUN mkdir -p /data /app/static/images

# Setze Berechtigungen für die Ordner
RUN chmod -R 755 /data /app/static

# Setze Umgebungsvariablen
ENV DATABASE_PATH=/data/car_data.db
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Port freigeben
EXPOSE 5000

# Start-Kommando
CMD ["python", "app.py"]
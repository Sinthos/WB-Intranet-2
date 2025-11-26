#!/bin/bash
#
# WB-Intranet 2 - Systemd Service Setup
# Dieses Skript richtet den Systemd-Service ein, damit die Anwendung
# automatisch beim Systemstart läuft.
#

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="wb-intranet"
APP_PORT=5000

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_error() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║           WB-Intranet 2 - Service Setup                     ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Prüfe Root-Rechte
if [[ $EUID -ne 0 ]]; then
    log_error "Dieses Skript muss als Root ausgeführt werden!"
    echo -e "Bitte führe aus: ${YELLOW}sudo bash setup_service.sh${NC}"
    exit 1
fi

# Prüfe ob app.py existiert
if [[ ! -f "${SCRIPT_DIR}/app.py" ]]; then
    log_error "app.py nicht gefunden in ${SCRIPT_DIR}"
    exit 1
fi

# Ermittle Python-Pfad
if [[ -d "${SCRIPT_DIR}/venv" ]]; then
    PYTHON_PATH="${SCRIPT_DIR}/venv/bin/python"
    VENV_PATH="${SCRIPT_DIR}/venv"
elif [[ -d "${SCRIPT_DIR}/.venv" ]]; then
    PYTHON_PATH="${SCRIPT_DIR}/.venv/bin/python"
    VENV_PATH="${SCRIPT_DIR}/.venv"
else
    log_info "Keine virtuelle Umgebung gefunden. Erstelle eine..."
    python3 -m venv "${SCRIPT_DIR}/venv"
    source "${SCRIPT_DIR}/venv/bin/activate"
    pip install --upgrade pip -q
    pip install -r "${SCRIPT_DIR}/requirements.txt" -q
    deactivate
    PYTHON_PATH="${SCRIPT_DIR}/venv/bin/python"
    VENV_PATH="${SCRIPT_DIR}/venv"
    log_success "Virtuelle Umgebung erstellt"
fi

log_info "Python-Pfad: ${PYTHON_PATH}"

# Stoppe existierenden Service falls vorhanden
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    log_info "Stoppe existierenden Service..."
    systemctl stop "$SERVICE_NAME"
fi

# Erstelle Systemd Service
log_info "Erstelle Systemd Service..."

cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=WB-Intranet 2 - Auto Berndl Intranet
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${SCRIPT_DIR}
Environment="PATH=${VENV_PATH}/bin:/usr/local/bin:/usr/bin:/bin"
Environment="FLASK_ENV=production"
ExecStart=${PYTHON_PATH} ${SCRIPT_DIR}/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

log_success "Service-Datei erstellt: /etc/systemd/system/${SERVICE_NAME}.service"

# Systemd neu laden
log_info "Lade Systemd-Konfiguration neu..."
systemctl daemon-reload

# Service aktivieren (Autostart)
log_info "Aktiviere Service für Autostart..."
systemctl enable ${SERVICE_NAME}.service

# Service starten
log_info "Starte Service..."
systemctl start ${SERVICE_NAME}.service

# Warte kurz und prüfe Status
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Service läuft!"
else
    log_error "Service konnte nicht gestartet werden!"
    echo ""
    echo "Logs anzeigen mit:"
    echo -e "  ${YELLOW}sudo journalctl -u ${SERVICE_NAME} -n 50${NC}"
    exit 1
fi

# Ermittle IP-Adresse
IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

# Abschlussinformationen
echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              Service erfolgreich eingerichtet!              ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}Zugriff auf die Anwendung:${NC}"
echo -e "  → http://${IP_ADDR}:${APP_PORT}"
echo -e "  → http://localhost:${APP_PORT}"
echo ""
echo -e "${BLUE}Nützliche Befehle:${NC}"
echo -e "  Status prüfen:     ${YELLOW}sudo systemctl status ${SERVICE_NAME}${NC}"
echo -e "  Logs anzeigen:     ${YELLOW}sudo journalctl -u ${SERVICE_NAME} -f${NC}"
echo -e "  Neustart:          ${YELLOW}sudo systemctl restart ${SERVICE_NAME}${NC}"
echo -e "  Stoppen:           ${YELLOW}sudo systemctl stop ${SERVICE_NAME}${NC}"
echo -e "  Deaktivieren:      ${YELLOW}sudo systemctl disable ${SERVICE_NAME}${NC}"
echo ""
echo -e "${GREEN}Die Anwendung startet jetzt automatisch beim Systemstart!${NC}"
echo ""

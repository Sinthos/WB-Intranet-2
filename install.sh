#!/bin/bash
#
# WB-Intranet 2 - 1-Klick-Installationsskript für Proxmox LXC
# Repository: https://github.com/Sinthos/WB-Intranet-2
#
# Verwendung:
#   bash <(curl -fsSL https://raw.githubusercontent.com/Sinthos/WB-Intranet-2/main/install.sh)
#
# Oder:
#   wget -qO- https://raw.githubusercontent.com/Sinthos/WB-Intranet-2/main/install.sh | bash
#

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
REPO_URL="https://github.com/Sinthos/WB-Intranet-2.git"
INSTALL_DIR="/opt/wb-intranet"
SERVICE_NAME="wb-intranet"
APP_PORT=5000
PYTHON_MIN_VERSION="3.9"

# Logging-Funktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

log_error() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

# Banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           WB-Intranet 2 - Installationsskript               ║"
    echo "║                                                              ║"
    echo "║           Für Proxmox LXC (Debian/Ubuntu)                   ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Prüfe Root-Rechte
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Dieses Skript muss als Root ausgeführt werden!"
        log_info "Bitte führe aus: sudo bash install.sh"
        exit 1
    fi
}

# Prüfe Betriebssystem
check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        log_info "Erkanntes Betriebssystem: $PRETTY_NAME"
    else
        log_error "Konnte Betriebssystem nicht erkennen!"
        exit 1
    fi

    case $OS in
        debian|ubuntu)
            log_success "Unterstütztes Betriebssystem erkannt"
            ;;
        *)
            log_warning "Nicht offiziell unterstütztes OS: $OS"
            log_warning "Die Installation wird fortgesetzt, kann aber fehlschlagen."
            ;;
    esac
}

# Aktualisiere Paketlisten
update_packages() {
    log_info "Aktualisiere Paketlisten..."
    apt-get update -qq
    log_success "Paketlisten aktualisiert"
}

# Installiere Abhängigkeiten
install_dependencies() {
    log_info "Installiere System-Abhängigkeiten..."
    
    # Basis-Pakete
    apt-get install -y -qq \
        curl \
        wget \
        git \
        ca-certificates \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info
    
    log_success "System-Abhängigkeiten installiert"
}

# Prüfe Python-Version
check_python() {
    log_info "Prüfe Python-Version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 nicht gefunden!"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Python-Version: $PYTHON_VERSION"
    
    # Vergleiche Versionen
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        log_success "Python-Version ist kompatibel"
    else
        log_error "Python $PYTHON_MIN_VERSION oder höher erforderlich!"
        exit 1
    fi
}

# Klone Repository
clone_repository() {
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "Installationsverzeichnis existiert bereits: $INSTALL_DIR"
        read -p "Möchten Sie es überschreiben? (j/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Jj]$ ]]; then
            log_info "Entferne altes Verzeichnis..."
            rm -rf "$INSTALL_DIR"
        else
            log_info "Aktualisiere bestehendes Repository..."
            cd "$INSTALL_DIR"
            git pull origin main || git pull origin master
            log_success "Repository aktualisiert"
            return
        fi
    fi

    log_info "Klone Repository nach $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    log_success "Repository geklont"
}

# Erstelle Datenverzeichnisse
create_directories() {
    log_info "Erstelle Datenverzeichnisse..."
    
    mkdir -p "$INSTALL_DIR/data"
    mkdir -p "$INSTALL_DIR/static/images"
    mkdir -p "$INSTALL_DIR/backups"
    
    # Berechtigungen setzen
    chmod -R 755 "$INSTALL_DIR/data"
    chmod -R 755 "$INSTALL_DIR/static"
    chmod -R 755 "$INSTALL_DIR/backups"
    
    log_success "Verzeichnisse erstellt"
}

# Erstelle virtuelle Umgebung und installiere Python-Abhängigkeiten
setup_python_env() {
    log_info "Erstelle virtuelle Python-Umgebung..."
    
    cd "$INSTALL_DIR"
    
    # Erstelle venv
    python3 -m venv venv
    
    # Aktiviere venv und installiere Abhängigkeiten
    source venv/bin/activate
    
    log_info "Aktualisiere pip..."
    pip install --upgrade pip -q
    
    log_info "Installiere Python-Abhängigkeiten..."
    pip install -r requirements.txt -q
    
    deactivate
    
    log_success "Python-Umgebung eingerichtet"
}

# Erstelle Systemd Service
create_systemd_service() {
    log_info "Erstelle Systemd Service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=WB-Intranet 2 - Auto Berndl Intranet
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Service aktivieren und starten
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}.service
    systemctl start ${SERVICE_NAME}.service
    
    log_success "Systemd Service erstellt und gestartet"
}

# Konfiguriere Firewall (falls ufw installiert)
configure_firewall() {
    if command -v ufw &> /dev/null; then
        log_info "Konfiguriere Firewall..."
        ufw allow ${APP_PORT}/tcp comment "WB-Intranet"
        log_success "Firewall-Regel hinzugefügt für Port ${APP_PORT}"
    else
        log_info "UFW nicht installiert - überspringe Firewall-Konfiguration"
    fi
}

# Warte auf Anwendung
wait_for_app() {
    log_info "Warte auf Anwendung..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:${APP_PORT} 2>/dev/null | grep -q "200\|302"; then
            log_success "Anwendung ist bereit!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    echo ""
    log_warning "Anwendung antwortet noch nicht - bitte manuell prüfen"
}

# Zeige Abschlussinformationen
print_completion() {
    # Ermittle IP-Adresse
    IP_ADDR=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           Installation erfolgreich abgeschlossen!           ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}Zugriff auf die Anwendung:${NC}"
    echo -e "  → http://${IP_ADDR}:${APP_PORT}"
    echo -e "  → http://localhost:${APP_PORT}"
    echo ""
    echo -e "${BLUE}Nützliche Befehle:${NC}"
    echo -e "  Status prüfen:     ${YELLOW}systemctl status ${SERVICE_NAME}${NC}"
    echo -e "  Logs anzeigen:     ${YELLOW}journalctl -u ${SERVICE_NAME} -f${NC}"
    echo -e "  Neustart:          ${YELLOW}systemctl restart ${SERVICE_NAME}${NC}"
    echo -e "  Update:            ${YELLOW}cd ${INSTALL_DIR} && bash update.sh${NC}"
    echo ""
    echo -e "${BLUE}Installationsverzeichnis:${NC} ${INSTALL_DIR}"
    echo -e "${BLUE}Datenbank:${NC} ${INSTALL_DIR}/data/car_data.db"
    echo -e "${BLUE}Logs:${NC} journalctl -u ${SERVICE_NAME}"
    echo ""
}

# Hauptfunktion
main() {
    print_banner
    
    log_info "Starte Installation..."
    echo ""
    
    check_root
    check_os
    update_packages
    install_dependencies
    check_python
    clone_repository
    create_directories
    setup_python_env
    create_systemd_service
    configure_firewall
    wait_for_app
    
    print_completion
}

# Skript ausführen
main "$@"

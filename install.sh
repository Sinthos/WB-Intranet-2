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
    log_info "Installiere Abhängigkeiten..."
    
    # Basis-Pakete
    apt-get install -y -qq \
        curl \
        wget \
        git \
        ca-certificates \
        gnupg \
        lsb-release \
        apt-transport-https \
        software-properties-common
    
    log_success "Basis-Abhängigkeiten installiert"
}

# Installiere Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker ist bereits installiert"
        docker --version
        return
    fi

    log_info "Installiere Docker..."
    
    # Docker GPG Key hinzufügen
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Docker Repository hinzufügen
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Docker installieren
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Docker starten und aktivieren
    systemctl start docker
    systemctl enable docker

    log_success "Docker installiert und gestartet"
    docker --version
}

# Installiere Docker Compose (falls nicht als Plugin vorhanden)
install_docker_compose() {
    if docker compose version &> /dev/null; then
        log_success "Docker Compose (Plugin) ist bereits installiert"
        docker compose version
        return
    fi

    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose (Standalone) ist bereits installiert"
        docker-compose --version
        return
    fi

    log_info "Installiere Docker Compose..."
    
    # Neueste Version ermitteln
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    
    # Docker Compose herunterladen
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    log_success "Docker Compose installiert"
    docker-compose --version
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
    
    # Berechtigungen setzen
    chmod -R 755 "$INSTALL_DIR/data"
    chmod -R 755 "$INSTALL_DIR/static"
    
    log_success "Verzeichnisse erstellt"
}

# Baue und starte Docker Container
start_application() {
    log_info "Baue und starte Docker Container..."
    
    cd "$INSTALL_DIR"
    
    # Docker Compose verwenden (Plugin oder Standalone)
    if docker compose version &> /dev/null; then
        docker compose build
        docker compose up -d
    else
        docker-compose build
        docker-compose up -d
    fi
    
    log_success "Anwendung gestartet"
}

# Erstelle Systemd Service
create_systemd_service() {
    log_info "Erstelle Systemd Service..."
    
    # Ermittle Docker Compose Befehl
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=WB-Intranet 2 - Auto Berndl Intranet
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${INSTALL_DIR}
ExecStart=${COMPOSE_CMD} up -d
ExecStop=${COMPOSE_CMD} down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    # Service aktivieren
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}.service
    
    log_success "Systemd Service erstellt und aktiviert"
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
    echo -e "  Logs anzeigen:     ${YELLOW}cd ${INSTALL_DIR} && docker compose logs -f${NC}"
    echo -e "  Neustart:          ${YELLOW}systemctl restart ${SERVICE_NAME}${NC}"
    echo -e "  Update:            ${YELLOW}cd ${INSTALL_DIR} && bash update.sh${NC}"
    echo ""
    echo -e "${BLUE}Installationsverzeichnis:${NC} ${INSTALL_DIR}"
    echo -e "${BLUE}Datenbank:${NC} ${INSTALL_DIR}/data/car_data.db"
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
    install_docker
    install_docker_compose
    clone_repository
    create_directories
    start_application
    create_systemd_service
    configure_firewall
    
    print_completion
}

# Skript ausführen
main "$@"

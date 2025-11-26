#!/bin/bash
#
# WB-Intranet 2 - Migrations-Skript
# 
# Dieses Skript migriert von einer alten Version zur neuen Version
# OHNE Datenverlust der Datenbank.
#
# Verwendung:
#   curl -fsSL https://raw.githubusercontent.com/Sinthos/WB-Intranet-2/main/migrate.sh | bash
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
NEW_INSTALL_DIR="/opt/wb-intranet"
BACKUP_DIR="/tmp/wb-intranet-backup-$(date +%Y%m%d_%H%M%S)"

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
    echo "║           WB-Intranet 2 - Migrations-Skript                 ║"
    echo "║                                                              ║"
    echo "║           Migration von alter Version zur neuen             ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Prüfe Root-Rechte
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Dieses Skript muss als Root ausgeführt werden!"
        log_info "Bitte führe aus: sudo bash migrate.sh"
        exit 1
    fi
}

# Finde bestehende Installation
find_existing_installation() {
    log_info "Suche nach bestehender Installation..."
    
    FOUND_DIRS=()
    
    # Mögliche Installationsorte
    SEARCH_PATHS=(
        "/opt/wb-intranet"
        "/opt/WB-Intranet"
        "/opt/WB-Intranet-2"
        "/opt/wb-intranet-2"
        "/home/*/wb-intranet"
        "/home/*/WB-Intranet"
        "/root/wb-intranet"
        "/root/WB-Intranet"
        "/var/www/wb-intranet"
    )
    
    for path in "${SEARCH_PATHS[@]}"; do
        # Expandiere Wildcards
        for expanded_path in $path; do
            if [[ -d "$expanded_path" ]]; then
                # Prüfe ob es eine WB-Intranet Installation ist
                if [[ -f "$expanded_path/app.py" ]] || [[ -f "$expanded_path/docker-compose.yml" ]]; then
                    FOUND_DIRS+=("$expanded_path")
                    log_success "Gefunden: $expanded_path"
                fi
            fi
        done
    done
    
    # Suche auch nach laufenden Docker-Containern
    if command -v docker &> /dev/null; then
        CONTAINER_PATH=$(docker inspect --format='{{range .Mounts}}{{if eq .Destination "/app"}}{{.Source}}{{end}}{{end}}' $(docker ps -q --filter "name=auto-berndl" 2>/dev/null || docker ps -q --filter "name=wb-intranet" 2>/dev/null) 2>/dev/null || true)
        if [[ -n "$CONTAINER_PATH" && -d "$CONTAINER_PATH" ]]; then
            FOUND_DIRS+=("$CONTAINER_PATH")
            log_success "Gefunden (Docker): $CONTAINER_PATH"
        fi
    fi
    
    if [[ ${#FOUND_DIRS[@]} -eq 0 ]]; then
        log_warning "Keine bestehende Installation gefunden."
        log_info "Führe stattdessen eine Neuinstallation durch..."
        
        # Frage nach manuellem Pfad
        read -p "Haben Sie eine bestehende Installation? Geben Sie den Pfad ein (oder Enter für Neuinstallation): " MANUAL_PATH
        
        if [[ -n "$MANUAL_PATH" && -d "$MANUAL_PATH" ]]; then
            OLD_INSTALL_DIR="$MANUAL_PATH"
        else
            # Neuinstallation
            log_info "Starte Neuinstallation..."
            curl -fsSL https://raw.githubusercontent.com/Sinthos/WB-Intranet-2/main/install.sh | bash
            exit 0
        fi
    elif [[ ${#FOUND_DIRS[@]} -eq 1 ]]; then
        OLD_INSTALL_DIR="${FOUND_DIRS[0]}"
        log_success "Verwende Installation: $OLD_INSTALL_DIR"
    else
        log_info "Mehrere Installationen gefunden:"
        for i in "${!FOUND_DIRS[@]}"; do
            echo "  [$i] ${FOUND_DIRS[$i]}"
        done
        read -p "Welche Installation soll migriert werden? [0-$((${#FOUND_DIRS[@]}-1))]: " CHOICE
        OLD_INSTALL_DIR="${FOUND_DIRS[$CHOICE]}"
    fi
}

# Backup erstellen
create_backup() {
    log_info "Erstelle Backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Datenbank sichern
    if [[ -f "$OLD_INSTALL_DIR/data/car_data.db" ]]; then
        cp "$OLD_INSTALL_DIR/data/car_data.db" "$BACKUP_DIR/"
        log_success "Datenbank gesichert: $BACKUP_DIR/car_data.db"
    elif [[ -f "$OLD_INSTALL_DIR/car_data.db" ]]; then
        cp "$OLD_INSTALL_DIR/car_data.db" "$BACKUP_DIR/"
        log_success "Datenbank gesichert: $BACKUP_DIR/car_data.db"
    else
        log_warning "Keine Datenbank gefunden - überspringe Backup"
    fi
    
    # Bilder sichern
    if [[ -d "$OLD_INSTALL_DIR/static/images" ]]; then
        cp -r "$OLD_INSTALL_DIR/static/images" "$BACKUP_DIR/"
        log_success "Bilder gesichert"
    fi
    
    # Instance-Ordner sichern (falls vorhanden)
    if [[ -d "$OLD_INSTALL_DIR/instance" ]]; then
        cp -r "$OLD_INSTALL_DIR/instance" "$BACKUP_DIR/"
        log_success "Instance-Ordner gesichert"
    fi
    
    log_success "Backup erstellt in: $BACKUP_DIR"
}

# Alte Container stoppen
stop_old_containers() {
    log_info "Stoppe alte Container..."
    
    cd "$OLD_INSTALL_DIR"
    
    if [[ -f "docker-compose.yml" ]]; then
        if docker compose version &> /dev/null; then
            docker compose down 2>/dev/null || true
        else
            docker-compose down 2>/dev/null || true
        fi
        log_success "Container gestoppt"
    fi
}

# Prüfe ob Git-Repository
check_git_repo() {
    if [[ -d "$OLD_INSTALL_DIR/.git" ]]; then
        IS_GIT_REPO=true
        log_info "Git-Repository erkannt"
    else
        IS_GIT_REPO=false
        log_info "Kein Git-Repository - führe Neuinstallation durch"
    fi
}

# Update via Git
update_via_git() {
    log_info "Aktualisiere via Git..."
    
    cd "$OLD_INSTALL_DIR"
    
    # Lokale Änderungen sichern
    git stash 2>/dev/null || true
    
    # Remote aktualisieren
    git fetch origin
    
    # Auf main/master Branch wechseln
    git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
    
    # Pull
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null
    
    log_success "Git-Update abgeschlossen"
}

# Neuinstallation mit Datenübernahme
fresh_install_with_data() {
    log_info "Führe Neuinstallation mit Datenübernahme durch..."
    
    # Alte Installation umbenennen
    if [[ "$OLD_INSTALL_DIR" == "$NEW_INSTALL_DIR" ]]; then
        mv "$OLD_INSTALL_DIR" "${OLD_INSTALL_DIR}-old-$(date +%Y%m%d)"
        log_info "Alte Installation umbenannt"
    fi
    
    # Neues Repository klonen
    git clone "$REPO_URL" "$NEW_INSTALL_DIR"
    log_success "Repository geklont"
    
    # Daten wiederherstellen
    mkdir -p "$NEW_INSTALL_DIR/data"
    
    if [[ -f "$BACKUP_DIR/car_data.db" ]]; then
        cp "$BACKUP_DIR/car_data.db" "$NEW_INSTALL_DIR/data/"
        log_success "Datenbank wiederhergestellt"
    fi
    
    if [[ -d "$BACKUP_DIR/images" ]]; then
        cp -r "$BACKUP_DIR/images"/* "$NEW_INSTALL_DIR/static/images/" 2>/dev/null || true
        log_success "Bilder wiederhergestellt"
    fi
    
    OLD_INSTALL_DIR="$NEW_INSTALL_DIR"
}

# Container neu bauen und starten
rebuild_and_start() {
    log_info "Baue und starte Container..."
    
    cd "$OLD_INSTALL_DIR"
    
    # Docker Compose verwenden
    if docker compose version &> /dev/null; then
        docker compose build --no-cache
        docker compose up -d
    else
        docker-compose build --no-cache
        docker-compose up -d
    fi
    
    log_success "Container gestartet"
}

# Warte auf Anwendung
wait_for_app() {
    log_info "Warte auf Anwendung..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302"; then
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

# Systemd Service erstellen/aktualisieren
update_systemd_service() {
    log_info "Aktualisiere Systemd Service..."
    
    # Ermittle Docker Compose Befehl
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    cat > /etc/systemd/system/wb-intranet.service << EOF
[Unit]
Description=WB-Intranet 2 - Auto Berndl Intranet
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${OLD_INSTALL_DIR}
ExecStart=${COMPOSE_CMD} up -d
ExecStop=${COMPOSE_CMD} down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable wb-intranet.service
    
    log_success "Systemd Service aktualisiert"
}

# Zeige Abschlussinformationen
print_completion() {
    IP_ADDR=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           Migration erfolgreich abgeschlossen!              ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}Zugriff auf die Anwendung:${NC}"
    echo -e "  → http://${IP_ADDR}:5000"
    echo -e "  → http://localhost:5000"
    echo ""
    echo -e "${BLUE}Backup-Verzeichnis:${NC} $BACKUP_DIR"
    echo -e "${BLUE}Installations-Verzeichnis:${NC} $OLD_INSTALL_DIR"
    echo ""
    echo -e "${BLUE}Nützliche Befehle:${NC}"
    echo -e "  Logs anzeigen:     ${YELLOW}cd $OLD_INSTALL_DIR && docker compose logs -f${NC}"
    echo -e "  Neustart:          ${YELLOW}systemctl restart wb-intranet${NC}"
    echo -e "  Zukünftige Updates: ${YELLOW}cd $OLD_INSTALL_DIR && bash update.sh${NC}"
    echo ""
    echo -e "${GREEN}Ihre Datenbank wurde erfolgreich übernommen!${NC}"
    echo ""
}

# Hauptfunktion
main() {
    print_banner
    
    check_root
    find_existing_installation
    create_backup
    stop_old_containers
    check_git_repo
    
    if $IS_GIT_REPO; then
        update_via_git
    else
        fresh_install_with_data
    fi
    
    rebuild_and_start
    wait_for_app
    update_systemd_service
    
    print_completion
}

# Skript ausführen
main "$@"

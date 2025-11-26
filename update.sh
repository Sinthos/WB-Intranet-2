#!/bin/bash
#
# WB-Intranet 2 - Update-Skript
# Repository: https://github.com/Sinthos/WB-Intranet-2
#
# Verwendung:
#   bash update.sh
#
# Dieses Skript:
# 1. Erstellt ein Backup der Datenbank
# 2. Zieht die neuesten Änderungen von GitHub
# 3. Baut den Docker-Container neu
# 4. Startet die Anwendung neu
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
BACKUP_DIR="${SCRIPT_DIR}/backups"
LOG_FILE="${SCRIPT_DIR}/update.log"
MAX_BACKUPS=10

# Logging-Funktionen
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" >> "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "INFO" "$1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
    log "OK" "$1"
}

log_warning() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
    log "WARNUNG" "$1"
}

log_error() {
    echo -e "${RED}[FEHLER]${NC} $1"
    log "FEHLER" "$1"
}

# Banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              WB-Intranet 2 - Update-Skript                  ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Prüfe ob wir im richtigen Verzeichnis sind
check_directory() {
    if [[ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]]; then
        log_error "docker-compose.yml nicht gefunden!"
        log_error "Bitte führe das Skript im WB-Intranet Verzeichnis aus."
        exit 1
    fi
    
    if [[ ! -d "${SCRIPT_DIR}/.git" ]]; then
        log_error "Kein Git-Repository gefunden!"
        log_error "Das Update-Skript benötigt ein geklontes Git-Repository."
        exit 1
    fi
    
    log_success "Verzeichnis geprüft: ${SCRIPT_DIR}"
}

# Ermittle Docker Compose Befehl
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        log_error "Docker Compose nicht gefunden!"
        exit 1
    fi
}

# Erstelle Backup der Datenbank
create_backup() {
    log_info "Erstelle Backup der Datenbank..."
    
    mkdir -p "$BACKUP_DIR"
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local db_file="${SCRIPT_DIR}/data/car_data.db"
    local backup_file="${BACKUP_DIR}/car_data_${timestamp}.db"
    
    if [[ -f "$db_file" ]]; then
        cp "$db_file" "$backup_file"
        log_success "Backup erstellt: $backup_file"
        
        # Alte Backups aufräumen (behalte nur die letzten MAX_BACKUPS)
        local backup_count=$(ls -1 "${BACKUP_DIR}"/car_data_*.db 2>/dev/null | wc -l)
        if [[ $backup_count -gt $MAX_BACKUPS ]]; then
            log_info "Räume alte Backups auf..."
            ls -1t "${BACKUP_DIR}"/car_data_*.db | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
            log_success "Alte Backups entfernt"
        fi
    else
        log_warning "Keine Datenbank gefunden - überspringe Backup"
    fi
}

# Hole aktuelle Version
get_current_version() {
    local version="unknown"
    local commit="unknown"
    
    if [[ -f "${SCRIPT_DIR}/VERSION" ]]; then
        version=$(cat "${SCRIPT_DIR}/VERSION" | tr -d '\n')
    fi
    
    if command -v git &> /dev/null; then
        commit=$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    fi
    
    echo "v${version} (${commit})"
}

# Prüfe auf Updates
check_updates() {
    log_info "Prüfe auf Updates..."
    
    cd "$SCRIPT_DIR"
    
    # Hole neueste Informationen vom Remote
    git fetch origin 2>/dev/null || {
        log_error "Konnte keine Verbindung zu GitHub herstellen"
        exit 1
    }
    
    # Ermittle den aktuellen Branch
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    # Prüfe ob Updates verfügbar sind
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/${current_branch} 2>/dev/null || git rev-parse origin/main 2>/dev/null || git rev-parse origin/master)
    
    if [[ "$local_commit" == "$remote_commit" ]]; then
        log_success "Die Anwendung ist bereits auf dem neuesten Stand!"
        echo ""
        echo -e "${GREEN}Aktuelle Version: $(get_current_version)${NC}"
        echo ""
        read -p "Möchten Sie trotzdem neu bauen? (j/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Jj]$ ]]; then
            exit 0
        fi
    else
        log_info "Update verfügbar!"
        echo ""
        echo -e "Aktuelle Version: ${YELLOW}$(get_current_version)${NC}"
        echo -e "Neueste Version:  ${GREEN}$(git log origin/${current_branch} -1 --format='%h' 2>/dev/null || git log origin/main -1 --format='%h')${NC}"
        echo ""
    fi
}

# Ziehe Updates von GitHub
pull_updates() {
    log_info "Ziehe Updates von GitHub..."
    
    cd "$SCRIPT_DIR"
    
    # Stash lokale Änderungen (falls vorhanden)
    local stash_result=$(git stash 2>&1)
    local had_changes=false
    if [[ ! "$stash_result" =~ "No local changes" ]]; then
        had_changes=true
        log_warning "Lokale Änderungen wurden temporär gespeichert"
    fi
    
    # Pull Updates
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || {
        log_error "Konnte Updates nicht herunterladen"
        if $had_changes; then
            git stash pop 2>/dev/null
        fi
        exit 1
    }
    
    # Stelle lokale Änderungen wieder her
    if $had_changes; then
        git stash pop 2>/dev/null || {
            log_warning "Konnte lokale Änderungen nicht wiederherstellen"
            log_warning "Bitte prüfen Sie: git stash list"
        }
    fi
    
    log_success "Updates heruntergeladen"
}

# Stoppe Container
stop_containers() {
    log_info "Stoppe laufende Container..."
    
    cd "$SCRIPT_DIR"
    local compose_cmd=$(get_compose_cmd)
    
    $compose_cmd down --remove-orphans 2>/dev/null || true
    
    log_success "Container gestoppt"
}

# Baue Container neu
build_containers() {
    log_info "Baue Container neu..."
    
    cd "$SCRIPT_DIR"
    local compose_cmd=$(get_compose_cmd)
    
    $compose_cmd build --no-cache
    
    log_success "Container gebaut"
}

# Starte Container
start_containers() {
    log_info "Starte Container..."
    
    cd "$SCRIPT_DIR"
    local compose_cmd=$(get_compose_cmd)
    
    $compose_cmd up -d
    
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

# Zeige Abschlussinformationen
print_completion() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              Update erfolgreich abgeschlossen!              ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}Neue Version:${NC} $(get_current_version)"
    echo ""
    echo -e "${BLUE}Zugriff:${NC} http://localhost:5000"
    echo ""
    echo -e "${BLUE}Logs anzeigen:${NC}"
    echo -e "  ${YELLOW}cd ${SCRIPT_DIR} && $(get_compose_cmd) logs -f${NC}"
    echo ""
}

# Rollback-Funktion
rollback() {
    log_error "Update fehlgeschlagen - versuche Rollback..."
    
    cd "$SCRIPT_DIR"
    local compose_cmd=$(get_compose_cmd)
    
    # Versuche Container zu starten (mit altem Image falls vorhanden)
    $compose_cmd up -d 2>/dev/null || true
    
    log_warning "Bitte prüfen Sie den Status manuell"
    exit 1
}

# Trap für Fehlerbehandlung
trap rollback ERR

# Hauptfunktion
main() {
    print_banner
    
    local start_time=$(date +%s)
    
    log_info "Starte Update-Prozess..."
    log "INFO" "========== Update gestartet =========="
    echo ""
    
    check_directory
    create_backup
    check_updates
    stop_containers
    pull_updates
    build_containers
    start_containers
    wait_for_app
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "Update abgeschlossen in ${duration} Sekunden"
    log "INFO" "========== Update beendet =========="
    
    print_completion
}

# Hilfe anzeigen
show_help() {
    echo "WB-Intranet 2 - Update-Skript"
    echo ""
    echo "Verwendung: bash update.sh [OPTION]"
    echo ""
    echo "Optionen:"
    echo "  -h, --help      Diese Hilfe anzeigen"
    echo "  -f, --force     Update ohne Bestätigung durchführen"
    echo "  -b, --backup    Nur Backup erstellen"
    echo "  --no-backup     Update ohne Backup durchführen"
    echo ""
}

# Parameter verarbeiten
FORCE_UPDATE=false
BACKUP_ONLY=false
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE_UPDATE=true
            shift
            ;;
        -b|--backup)
            BACKUP_ONLY=true
            shift
            ;;
        --no-backup)
            SKIP_BACKUP=true
            shift
            ;;
        *)
            log_error "Unbekannte Option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Nur Backup?
if $BACKUP_ONLY; then
    print_banner
    check_directory
    create_backup
    log_success "Backup abgeschlossen"
    exit 0
fi

# Skript ausführen
main

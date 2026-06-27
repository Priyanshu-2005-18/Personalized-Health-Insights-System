#!/usr/bin/env bash
# =============================================================================
#  Health Insights System — Deployment & Operations Script
#
#  Usage
#  -----
#    ./scripts/deploy.sh [command]
#
#  Commands
#  --------
#    setup       First-run: copy .env, generate SSL cert, train model
#    up          Build images and start all services
#    down        Stop all services (keeps volumes)
#    restart     Rolling restart of API and frontend only
#    logs        Tail logs for all services (or pass a service name)
#    ps          Show status of all containers
#    shell-api   Open a bash shell inside the API container
#    shell-db    Open a psql shell inside postgres
#    backup-db   Dump the database to ./backups/
#    restore-db  Restore from a dump file (pass path as second arg)
#    test        Run the test suite inside a temporary container
#    clean       Remove stopped containers and dangling images
#    help        Show this message
# =============================================================================

set -euo pipefail

COMPOSE="docker compose -f $(dirname "$0")/../docker-compose.yml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$DEPLOY_DIR/backups"
ENV_FILE="$DEPLOY_DIR/.env"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; RESET='\033[0m'
info()  { echo -e "${CYAN}[INFO]${RESET}  $*"; }
ok()    { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error() { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }

# ── Sanity checks ─────────────────────────────────────────────────────────────
require_cmd() { command -v "$1" &>/dev/null || error "'$1' is required but not installed."; }
require_cmd docker
require_cmd openssl

# ── Commands ──────────────────────────────────────────────────────────────────

cmd_setup() {
    info "Running first-time setup…"

    # 1. Copy .env
    if [[ ! -f "$ENV_FILE" ]]; then
        cp "$DEPLOY_DIR/.env.example" "$ENV_FILE"
        warn ".env created from .env.example — fill in secrets before continuing."
        warn "Edit $ENV_FILE then re-run: ./scripts/deploy.sh up"
        exit 0
    fi

    # 2. Generate self-signed SSL certificate (replace with Let's Encrypt in prod)
    SSL_DIR="$DEPLOY_DIR/nginx/ssl"
    if [[ ! -f "$SSL_DIR/self-signed.crt" ]]; then
        info "Generating self-signed TLS certificate…"
        mkdir -p "$SSL_DIR"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/self-signed.key" \
            -out    "$SSL_DIR/self-signed.crt" \
            -subj   "/C=US/ST=State/L=City/O=HealthInsights/CN=localhost" \
            2>/dev/null
        ok "Self-signed cert generated at $SSL_DIR/"
    fi

    # 3. Create backup directory
    mkdir -p "$BACKUP_DIR"

    ok "Setup complete. Run './scripts/deploy.sh up' to start."
}

cmd_up() {
    [[ -f "$ENV_FILE" ]] || error ".env not found. Run './scripts/deploy.sh setup' first."

    info "Building images…"
    $COMPOSE build --pull

    info "Starting services…"
    $COMPOSE up -d

    info "Waiting for health checks…"
    sleep 5
    $COMPOSE ps

    ok "Services started. API: https://localhost/api/v1/health"
    ok "Swagger docs:         https://localhost/docs"
}

cmd_down() {
    info "Stopping services…"
    $COMPOSE down
    ok "All services stopped (volumes preserved)."
}

cmd_restart() {
    info "Rolling restart of api and frontend…"
    $COMPOSE restart api frontend
    ok "Done."
}

cmd_logs() {
    SERVICE="${2:-}"
    $COMPOSE logs -f --tail=100 $SERVICE
}

cmd_ps() {
    $COMPOSE ps
}

cmd_shell_api() {
    $COMPOSE exec api bash
}

cmd_shell_db() {
    source "$ENV_FILE"
    $COMPOSE exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
}

cmd_backup_db() {
    source "$ENV_FILE"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    DUMP_FILE="$BACKUP_DIR/health_insights_${TIMESTAMP}.pgdump"

    info "Dumping database to $DUMP_FILE …"
    $COMPOSE exec -T postgres pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -Fc \
        > "$DUMP_FILE"
    ok "Backup saved: $DUMP_FILE"
}

cmd_restore_db() {
    DUMP_FILE="${2:-}"
    [[ -f "$DUMP_FILE" ]] || error "Usage: $0 restore-db /path/to/dump.pgdump"
    source "$ENV_FILE"

    warn "This will DROP and restore the database. Are you sure? [y/N]"
    read -r CONFIRM
    [[ "$CONFIRM" =~ ^[Yy]$ ]] || { info "Aborted."; exit 0; }

    info "Restoring from $DUMP_FILE …"
    $COMPOSE exec -T postgres pg_restore \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --clean --if-exists \
        < "$DUMP_FILE"
    ok "Restore complete."
}

cmd_test() {
    info "Running test suite…"
    $COMPOSE run --rm --no-deps api \
        sh -c "pip install pytest httpx -q && pytest tests/test_api.py -v"
}

cmd_clean() {
    info "Removing stopped containers and dangling images…"
    docker container prune -f
    docker image prune -f
    ok "Clean complete."
}

cmd_help() {
    sed -n '/^#  Commands/,/^# ====/p' "$0" | head -n -1 | sed 's/^#  \?//'
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
COMMAND="${1:-help}"
case "$COMMAND" in
    setup)      cmd_setup ;;
    up)         cmd_up ;;
    down)       cmd_down ;;
    restart)    cmd_restart ;;
    logs)       cmd_logs "$@" ;;
    ps)         cmd_ps ;;
    shell-api)  cmd_shell_api ;;
    shell-db)   cmd_shell_db ;;
    backup-db)  cmd_backup_db ;;
    restore-db) cmd_restore_db "$@" ;;
    test)       cmd_test ;;
    clean)      cmd_clean ;;
    help|--help|-h) cmd_help ;;
    *)          error "Unknown command: $COMMAND. Run '$0 help' for usage." ;;
esac

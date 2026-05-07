#!/usr/bin/env bash
# install.sh — one-command setup for security-ai-eval-lab
#
# Usage:
#   ./install.sh                  # interactive: prompts for missing secrets
#   OPENAI_API_KEY=sk-... REGISTRY_TOKEN=ghp_... ./install.sh  # non-interactive
#
# What it does:
#   1. Checks prerequisites (Docker, Docker Compose)
#   2. Creates .env from .env.sample if not present; fills in secrets
#   3. Starts Postgres and waits for it to be healthy
#   4. Runs Alembic migrations (reliability schema, then security_eval schema)
#   5. Runs a dry-run evaluation as a smoke test
#   6. Prints next-step instructions

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[install]${NC} $*"; }
success() { echo -e "${GREEN}[install]${NC} $*"; }
warn()    { echo -e "${YELLOW}[install]${NC} $*"; }
die()     { echo -e "${RED}[install] ERROR:${NC} $*" >&2; exit 1; }

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

get_env_value() {
    local key="$1"
    local current_value="${!key:-}"
    local line value

    if [[ -n "$current_value" ]]; then
        printf '%s' "$current_value"
        return 0
    fi

    if [[ -f .env ]]; then
        line="$(grep -E "^[[:space:]]*${key}=" .env | tail -n 1 || true)"
        value="${line#*=}"
        value="${value%$'\r'}"
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        printf '%s' "$value"
    fi
}

set_env_value() {
    local key="$1"
    local value="$2"
    local tmp_file

    tmp_file="$(mktemp)"
    awk -v key="$key" -v value="$value" '
        BEGIN { updated = 0 }
        $0 ~ "^[[:space:]]*" key "=" {
            print key "=" value
            updated = 1
            next
        }
        { print }
        END {
            if (!updated) {
                print key "=" value
            }
        }
    ' .env > "$tmp_file"
    mv "$tmp_file" .env
}

# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
info "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || die "Docker is not installed. Install from https://docs.docker.com/get-docker/"

# Accept both 'docker compose' (plugin) and 'docker-compose' (standalone)
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    die "Docker Compose is not installed. Install from https://docs.docker.com/compose/install/"
fi

success "Docker $(docker --version | awk '{print $3}' | tr -d ',') + Compose ready"

# ── Step 2: .env setup ────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
    info "Creating .env from .env.sample..."
    umask 077
    cp .env.sample .env
fi

chmod 600 .env

POSTGRES_USER="$(get_env_value POSTGRES_USER)"
POSTGRES_PASSWORD="$(get_env_value POSTGRES_PASSWORD)"
POSTGRES_DB="$(get_env_value POSTGRES_DB)"
OPENAI_API_KEY="$(get_env_value OPENAI_API_KEY)"
REGISTRY_TOKEN="$(get_env_value REGISTRY_TOKEN)"
AI_RELIABILITY_FW_VERSION="$(get_env_value AI_RELIABILITY_FW_VERSION)"
AI_RELIABILITY_FW_WHEEL_URL="$(get_env_value AI_RELIABILITY_FW_WHEEL_URL)"
AI_RELIABILITY_FW_WHEEL_SHA256="$(get_env_value AI_RELIABILITY_FW_WHEEL_SHA256)"
export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB OPENAI_API_KEY REGISTRY_TOKEN
export AI_RELIABILITY_FW_VERSION AI_RELIABILITY_FW_WHEEL_URL AI_RELIABILITY_FW_WHEEL_SHA256
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

if [[ -z "${AI_RELIABILITY_FW_VERSION:-}" ]]; then
    AI_RELIABILITY_FW_VERSION="0.2.1"
fi
if [[ -z "${AI_RELIABILITY_FW_WHEEL_URL:-}" ]]; then
    AI_RELIABILITY_FW_WHEEL_URL="https://github.com/ngallodev-software/ai-reliability-fw/releases/download/v${AI_RELIABILITY_FW_VERSION}/ai_reliability_fw-${AI_RELIABILITY_FW_VERSION}-py3-none-any.whl"
fi

# Prompt for OPENAI_API_KEY if not set or still placeholder
if [[ -z "${OPENAI_API_KEY:-}" || "${OPENAI_API_KEY:-}" == "sk-REPLACE_ME" ]]; then
    if [[ -t 0 ]]; then
        echo -e "${YELLOW}[install]${NC} OPENAI_API_KEY is required for live evaluation runs."
        read -rsp "         Enter your OpenAI API key (sk-...), or press Enter to skip: " input_key
        echo
        if [[ -n "$input_key" ]]; then
            OPENAI_API_KEY="$input_key"
            set_env_value OPENAI_API_KEY "$input_key"
        else
            warn "OPENAI_API_KEY not set — dry-run mode will work but live evaluation requires it."
        fi
    else
        warn "OPENAI_API_KEY not set — running in non-interactive mode. Live evaluation will not work."
    fi
fi

# Prompt for REGISTRY_TOKEN if not set or still placeholder
if [[ -z "${REGISTRY_TOKEN:-}" || "${REGISTRY_TOKEN:-}" == "REPLACE_ME" ]]; then
    if [[ -t 0 ]]; then
        echo -e "${YELLOW}[install]${NC} REGISTRY_TOKEN is required to fetch the ai-reliability-fw wheel."
        echo    "         Create a GitHub PAT (classic, repo scope) at: github.com/settings/tokens"
        read -rsp "         Enter your GitHub PAT (ghp_...): " input_token
        echo
        if [[ -n "$input_token" ]]; then
            REGISTRY_TOKEN="$input_token"
            set_env_value REGISTRY_TOKEN "$input_token"
        else
            die "REGISTRY_TOKEN is required to build the Docker image. Aborting."
        fi
    else
        die "REGISTRY_TOKEN is not set. Export it before running: REGISTRY_TOKEN=ghp_... ./install.sh"
    fi
fi

# Prompt for AI_RELIABILITY_FW_WHEEL_SHA256 if not set or still placeholder
if [[ -z "${AI_RELIABILITY_FW_WHEEL_SHA256:-}" || "${AI_RELIABILITY_FW_WHEEL_SHA256:-}" == "REPLACE_ME" ]]; then
    if [[ -t 0 ]]; then
        echo -e "${YELLOW}[install]${NC} AI_RELIABILITY_FW_WHEEL_SHA256 is required to verify the ai-reliability-fw wheel."
        echo    "         Resolve it from a trusted source for:"
        echo    "         ${AI_RELIABILITY_FW_WHEEL_URL}"
        read -rp "         Enter the trusted SHA-256 digest: " input_sha
        if [[ -n "$input_sha" ]]; then
            AI_RELIABILITY_FW_WHEEL_SHA256="$input_sha"
            set_env_value AI_RELIABILITY_FW_WHEEL_SHA256 "$input_sha"
        else
            die "AI_RELIABILITY_FW_WHEEL_SHA256 is required to verify the wheel. Aborting."
        fi
    else
        die "AI_RELIABILITY_FW_WHEEL_SHA256 is not set. Export it before running install.sh."
    fi
fi

success ".env ready"

# ── Step 3: Start Postgres ────────────────────────────────────────────────────
info "Starting Postgres..."
$COMPOSE up db -d

info "Waiting for Postgres to be healthy..."
MAX_WAIT=60
ELAPSED=0
until $COMPOSE exec -T db pg_isready -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-shared_db}" >/dev/null 2>&1; do
    if [[ $ELAPSED -ge $MAX_WAIT ]]; then
        die "Postgres did not become healthy within ${MAX_WAIT}s."
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done
success "Postgres healthy"

# ── Step 4: Migrations ────────────────────────────────────────────────────────
info "Building app image (this installs the ai-reliability-fw wheel)..."
$COMPOSE build migrate

info "Running Alembic migrations..."
$COMPOSE --profile migrate up migrate
success "Migrations complete"

# ── Step 5: Smoke test ────────────────────────────────────────────────────────
info "Running dry-run smoke test..."
$COMPOSE run --rm \
    -e DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-user}:${POSTGRES_PASSWORD:-pass}@db:5432/${POSTGRES_DB:-shared_db}" \
    eval-lab \
    python -m evaluation.runner --dataset datasets/ --name install-smoke-test --dry-run

success "Smoke test passed"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  security-ai-eval-lab is ready${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Quickstart (no DB, no API key):"
echo "    python3 -m examples.run_eval"
echo ""
echo "  Dry-run evaluation (DB, no API key):"
echo "    python3 -m evaluation.runner --dataset datasets/ --name test --dry-run"
echo ""

if [[ -n "${OPENAI_API_KEY:-}" && "${OPENAI_API_KEY:-}" != "sk-REPLACE_ME" ]]; then
    echo "  Live evaluation (DB + OpenAI):"
    echo "    docker compose run --rm eval-lab \\"
    echo "      python -m evaluation.runner --dataset datasets/ --name live-001 --model gpt-4o-mini"
else
    echo "  Live evaluation (requires OPENAI_API_KEY in .env):"
    echo "    # Add OPENAI_API_KEY to .env, then:"
    echo "    docker compose run --rm eval-lab \\"
    echo "      python -m evaluation.runner --dataset datasets/ --name live-001 --model gpt-4o-mini"
fi

echo ""
echo "  Stop Postgres:"
echo "    docker compose down"
echo ""

#!/usr/bin/env bash
# bootstrap-ec2.sh — provision boolean-algebra-engine on a fresh Ubuntu EC2 instance
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Shrivastava-Aditya/bool-LLM-ngn/master/scripts/bootstrap-ec2.sh | bash
#   # or clone first, then:
#   bash scripts/bootstrap-ec2.sh [--docker] [--api] [--dev]
#
# Flags:
#   --docker   Install via Docker Compose (includes Ollama)
#   --api      Install and run the FastAPI server as a systemd service
#   --dev      Install dev dependencies (pytest, ruff, etc.)
#
# After running, the API is available at http://localhost:8000 (or your EC2 public IP).

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/Shrivastava-Aditya/bool-LLM-ngn.git"
INSTALL_DIR="$HOME/boolean-algebra-engine"
PYTHON_MIN="3.11"
SERVICE_NAME="boolcalc-api"
API_PORT=8000

MODE_DOCKER=false
MODE_API=false
MODE_DEV=false

for arg in "$@"; do
  case $arg in
    --docker) MODE_DOCKER=true ;;
    --api)    MODE_API=true    ;;
    --dev)    MODE_DEV=true    ;;
  esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────
info()  { echo -e "\033[1;34m[bootstrap]\033[0m $*"; }
ok()    { echo -e "\033[1;32m[ok]\033[0m $*"; }
warn()  { echo -e "\033[1;33m[warn]\033[0m $*"; }
die()   { echo -e "\033[1;31m[error]\033[0m $*" >&2; exit 1; }

require_root() {
  [[ $EUID -ne 0 ]] && die "Run as root or with sudo for system-level installs."
}

# ── System packages ──────────────────────────────────────────────────────────
info "Updating apt and installing system packages..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -q
sudo apt-get install -y -q \
  curl git unzip build-essential \
  python3 python3-pip python3-venv python3-dev \
  libssl-dev libffi-dev \
  ca-certificates gnupg lsb-release

# ── Python version check ─────────────────────────────────────────────────────
PYTHON_BIN="python3"
PY_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [[ $PY_MAJOR -lt 3 || ($PY_MAJOR -eq 3 && $PY_MINOR -lt 10) ]]; then
  info "System Python ($PY_VERSION) < 3.10 — installing Python $PYTHON_MIN via deadsnakes PPA..."
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update -q
  sudo apt-get install -y -q "python${PYTHON_MIN}" "python${PYTHON_MIN}-venv" "python${PYTHON_MIN}-dev"
  PYTHON_BIN="python${PYTHON_MIN}"
fi

ok "Using $($PYTHON_BIN --version)"

# ── Docker path ──────────────────────────────────────────────────────────────
if $MODE_DOCKER; then
  info "Installing Docker..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"

  info "Installing Docker Compose plugin..."
  sudo apt-get install -y -q docker-compose-plugin

  info "Cloning repo..."
  [[ -d "$INSTALL_DIR" ]] || git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  git pull --ff-only

  info "Writing .env (edit with your API keys before starting)..."
  if [[ ! -f .env ]]; then
    cat > .env <<'ENV'
# Fill in your keys — only ANTHROPIC_API_KEY or OPENAI_API_KEY is required for NL mode
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
# Optional Redis cache
# REDIS_URL=redis://redis:6379
ENV
    warn "Created .env — add your API keys before starting."
  fi

  info "Starting services (API + Ollama)..."
  sudo docker compose up -d --build

  ok "Done. API → http://$(curl -sf https://api.ipify.org || echo 'your-ec2-ip'):${API_PORT}"
  ok "Ollama → http://$(curl -sf https://api.ipify.org || echo 'your-ec2-ip'):11434"
  echo
  warn "First Ollama model pull may take a few minutes."
  warn "If you added yourself to the docker group, log out and back in first: newgrp docker"
  exit 0
fi

# ── Standard (venv) path ─────────────────────────────────────────────────────
info "Cloning repo to $INSTALL_DIR..."
[[ -d "$INSTALL_DIR" ]] || git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"
git pull --ff-only

info "Creating virtual environment..."
$PYTHON_BIN -m venv .venv
source .venv/bin/activate

info "Installing package..."
pip install --upgrade pip -q

if $MODE_DEV; then
  pip install -e ".[cli,nl-anthropic,nl-openai]" -q
  pip install pytest ruff mypy -q
  ok "Dev dependencies installed."
else
  pip install "boolean-algebra-engine[cli,nl-anthropic]" -q
fi

# ── .env ─────────────────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
  cp .env.example .env 2>/dev/null || cat > .env <<'ENV'
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OLLAMA_HOST=http://localhost:11434
# REDIS_URL=redis://localhost:6379
ENV
  warn "Created .env — fill in your API keys."
fi

# ── Verify CLI ───────────────────────────────────────────────────────────────
info "Verifying CLI..."
boolcalc --version && ok "boolcalc CLI works."

# ── API systemd service ───────────────────────────────────────────────────────
if $MODE_API; then
  info "Creating systemd service: $SERVICE_NAME..."
  VENV_BIN="$INSTALL_DIR/.venv/bin"

  sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<SERVICE
[Unit]
Description=Boolean Algebra Engine API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$VENV_BIN/uvicorn boolean_algebra_engine.api.main:app --host 0.0.0.0 --port $API_PORT
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

  sudo systemctl daemon-reload
  sudo systemctl enable "$SERVICE_NAME"
  sudo systemctl restart "$SERVICE_NAME"

  sleep 2
  if systemctl is-active --quiet "$SERVICE_NAME"; then
    ok "Service running → http://$(curl -sf https://api.ipify.org || echo 'your-ec2-ip'):${API_PORT}"
    ok "Manage: sudo systemctl {status,restart,stop} $SERVICE_NAME"
    ok "Logs:   journalctl -u $SERVICE_NAME -f"
  else
    warn "Service may not have started. Check: journalctl -u $SERVICE_NAME -n 50"
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo
ok "Bootstrap complete."
echo
echo "  Next steps:"
if $MODE_DEV; then
  echo "    source $INSTALL_DIR/.venv/bin/activate"
  echo "    pytest tests/"
elif $MODE_API; then
  echo "    Edit $INSTALL_DIR/.env with your API keys, then:"
  echo "    sudo systemctl restart $SERVICE_NAME"
else
  echo "    source $INSTALL_DIR/.venv/bin/activate"
  echo "    boolcalc \"A + B\""
  echo "    boolcalc ask \"simplify majority gate for 3 inputs\""
fi
echo
echo "  Open source: https://github.com/Shrivastava-Aditya/bool-LLM-ngn"

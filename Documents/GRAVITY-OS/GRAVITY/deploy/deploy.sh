#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────
# Gravity — fresh Hetzner Ubuntu 24.04 deploy
# ─────────────────────────────────────────────

REPO_URL="https://github.com/YOUR_ORG/GRAVITY.git"
APP_DIR="/opt/gravity"

echo ""
echo "======================================="
echo "  Gravity Production Deploy Script"
echo "======================================="
echo ""

# ── 0. Must run as root (or with sudo) ──────
if [[ $EUID -ne 0 ]]; then
  echo "ERROR: Please run as root or with sudo." >&2
  exit 1
fi

# ── 1. Install Docker ────────────────────────
echo "[1/9] Installing Docker..."
if ! command -v docker &>/dev/null; then
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
  echo "  Docker installed."
else
  echo "  Docker already installed, skipping."
fi

# ── 2. Clone or pull repo ───────────────────
echo "[2/9] Setting up repository at $APP_DIR..."
if [[ -d "$APP_DIR/.git" ]]; then
  echo "  Repo exists — pulling latest..."
  git -C "$APP_DIR" pull
else
  git clone "$REPO_URL" "$APP_DIR"
  echo "  Repo cloned."
fi

cd "$APP_DIR/GRAVITY/deploy"

# ── 3. Configure .env ───────────────────────
echo "[3/9] Configuring environment..."
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo ""
  echo "  ┌─────────────────────────────────────────────────────────────┐"
  echo "  │  IMPORTANT: Edit .env before continuing!                    │"
  echo "  │                                                             │"
  echo "  │  At minimum set:                                            │"
  echo "  │    POSTGRES_PASSWORD  — strong random password              │"
  echo "  │    DATABASE_URL       — update password to match above      │"
  echo "  │    SECRET_KEY         — run: openssl rand -hex 32           │"
  echo "  │    GROQ_API_KEY or ANTHROPIC_API_KEY                        │"
  echo "  │    DOMAIN             — your actual domain name             │"
  echo "  └─────────────────────────────────────────────────────────────┘"
  echo ""
  read -r -p "  Press ENTER once you've finished editing .env..."
else
  echo "  .env already exists, skipping."
fi

# Read DOMAIN from .env
DOMAIN=$(grep -E '^DOMAIN=' .env | cut -d= -f2 | tr -d '[:space:]')
if [[ -z "$DOMAIN" || "$DOMAIN" == "yourdomain.com" ]]; then
  read -r -p "  Enter your domain name (e.g. api.gravity.app): " DOMAIN
  sed -i "s/^DOMAIN=.*/DOMAIN=${DOMAIN}/" .env
fi
echo "  Domain: $DOMAIN"

# ── 4. Create certbot directories ───────────
echo "[4/9] Creating certbot directories..."
mkdir -p certbot/conf certbot/www

# ── 5. Start Postgres and Redis first ───────
echo "[5/9] Starting Postgres and Redis..."
docker compose -f docker-compose.prod.yml up -d postgres redis
echo "  Waiting for Postgres to be healthy..."
sleep 8

# ── 6. Run DB migrations ────────────────────
echo "[6/9] Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm \
  -e DATABASE_URL="$(grep -E '^DATABASE_URL=' .env | cut -d= -f2-)" \
  api sh -c "
    cd /app && \
    if command -v alembic &>/dev/null && [ -f alembic.ini ]; then
      alembic upgrade head
    else
      python -c 'from backend.database import init_db; import asyncio; asyncio.run(init_db())' 2>/dev/null \
        || echo \"No migration runner found — skipping (tables may auto-create on startup).\"
    fi
  " || echo "  Migration step skipped (will retry on app startup)."

# ── 7. Obtain SSL certificate ───────────────
echo "[7/9] Obtaining SSL certificate for $DOMAIN..."

# Temporarily start nginx on port 80 only for the challenge
# We use a minimal inline config since the real nginx.conf needs certs first
docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -p 80:80 \
  nginx:alpine \
  sh -c "
    mkdir -p /var/www/certbot && \
    nginx -g 'daemon off;' &
    sleep 2 && \
    docker run --rm \
      certbot/certbot certonly \
      --webroot \
      -w /var/www/certbot \
      -d ${DOMAIN} \
      --email admin@${DOMAIN} \
      --agree-tos \
      --non-interactive
  " 2>/dev/null || true

# Preferred: run certbot standalone if webroot nginx dance fails
if [[ ! -f "certbot/conf/live/${DOMAIN}/fullchain.pem" ]]; then
  echo "  Running certbot standalone (port 80 must be free)..."
  docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    -p 80:80 \
    certbot/certbot certonly \
    --standalone \
    -d "$DOMAIN" \
    --email "admin@${DOMAIN}" \
    --agree-tos \
    --non-interactive
fi

# Patch nginx.conf with actual domain
sed -i "s/YOURDOMAIN/${DOMAIN}/g" nginx.conf
echo "  SSL certificate obtained and nginx.conf updated."

# ── 8. Bring up all services ────────────────
echo "[8/9] Starting all services..."
docker compose -f docker-compose.prod.yml up -d --build

# ── 9. Done ─────────────────────────────────
echo ""
echo "[9/9] Deploy complete!"
echo ""
echo "  Gravity API is running at: https://${DOMAIN}"
echo ""
echo "  Useful commands:"
echo "    Logs:    docker compose -f ${APP_DIR}/GRAVITY/deploy/docker-compose.prod.yml logs -f api"
echo "    Status:  docker compose -f ${APP_DIR}/GRAVITY/deploy/docker-compose.prod.yml ps"
echo "    Restart: docker compose -f ${APP_DIR}/GRAVITY/deploy/docker-compose.prod.yml restart api"
echo ""

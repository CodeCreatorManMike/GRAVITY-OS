# Gravity — Production Deployment

## Prerequisites

- **Server**: Hetzner CPX21 (2 vCPU / 4 GB RAM) running Ubuntu 24.04
- **Domain**: A/AAAA record for your domain pointing at the VPS public IP
- **Ports open**: 22 (SSH), 80 (HTTP), 443 (HTTPS)

---

## 1. First Deploy

SSH into your VPS as root, then:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/GRAVITY/main/GRAVITY/deploy/deploy.sh | bash
```

Or clone the repo manually and run:

```bash
git clone https://github.com/YOUR_ORG/GRAVITY.git /opt/gravity
cd /opt/gravity/GRAVITY/deploy
chmod +x deploy.sh
sudo ./deploy.sh
```

The script will:
1. Install Docker and the Compose plugin
2. Clone or update the repository
3. Prompt you to fill in `.env` (copy from `.env.example`)
4. Create certbot directories
5. Start Postgres and Redis, then run DB migrations
6. Obtain a Let's Encrypt SSL certificate for your domain
7. Start all services (nginx, api, certbot auto-renewal)

After the script finishes, the API is live at `https://YOURDOMAIN`.

---

## 2. SSL Renewal

Renewal is fully automatic. The `certbot` service runs in the background and attempts renewal every 12 hours. Certificates are renewed when they have fewer than 30 days remaining.

To check renewal status manually:

```bash
docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml run --rm certbot renew --dry-run
```

---

## 3. Updating the App

```bash
cd /opt/gravity
git pull
docker compose -f GRAVITY/deploy/docker-compose.prod.yml up -d --build api
```

This rebuilds and restarts only the API container with zero-downtime rolling restart (gunicorn handles graceful shutdown).

---

## 4. Viewing Logs

```bash
# API logs (live)
docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml logs -f api

# All services
docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml logs -f

# Nginx access/error logs
docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml logs -f nginx
```

---

## 5. Database Backup

```bash
# Dump to a local file
docker exec $(docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml ps -q postgres) \
  pg_dump -U gravity gravity > gravity_backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from dump
docker exec -i $(docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml ps -q postgres) \
  psql -U gravity gravity < gravity_backup_YYYYMMDD_HHMMSS.sql
```

---

## 6. Environment Variables

Copy `.env.example` to `.env` and fill in all values before deploying:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Strong random password for the DB |
| `SECRET_KEY` | JWT signing key — generate with `openssl rand -hex 32` |
| `GROQ_API_KEY` or `ANTHROPIC_API_KEY` | AI provider credentials |
| `DOMAIN` | Your public domain name |

---

## 7. Service Status

```bash
docker compose -f /opt/gravity/GRAVITY/deploy/docker-compose.prod.yml ps
```

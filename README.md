# Health Insights System — Deployment Guide

Full production deployment for the Health Insights platform using Docker Compose.

---

## Architecture

```
Internet
   │
   ▼
┌──────────┐   :80/:443
│  Nginx   │──────────────────────────────┐
│ (proxy)  │                              │
└──────────┘                              │
      │                                   │
      │ /api/*                            │ /  (SPA)
      ▼                                   ▼
┌──────────┐    backend_net    ┌──────────────────┐
│ FastAPI  │──────────────────▶│ React (Nginx)    │
│   API    │                   │  frontend        │
└──────────┘                   └──────────────────┘
      │
      ├──── PostgreSQL  (backend_net, port 5432)
      └──── Redis       (backend_net, port 6379)
```

**Networks**
- `backend_net` — internal only (API ↔ Postgres ↔ Redis). Not reachable from outside.
- `frontend_net` — Nginx ↔ API ↔ Frontend. Nginx is the only publicly bound container.

---

## File structure

```
deploy/
├── Dockerfile.api            # FastAPI multi-stage build
├── Dockerfile.frontend       # React + Nginx multi-stage build
├── docker-compose.yml        # All services
├── .env.example              # Environment variable template
├── nginx/
│   ├── nginx.conf            # Main Nginx config
│   └── conf.d/
│       ├── app.conf          # Reverse proxy + SSL (outer)
│       └── frontend.conf     # React SPA server (inner)
├── postgres/
│   ├── postgresql.conf       # Tuned Postgres config
│   └── init/
│       └── 01_schema.sql     # Schema, indexes, RLS, audit log
├── monitoring/
│   └── prometheus.yml        # Prometheus scrape config
├── scripts/
│   └── deploy.sh             # Operations helper script
└── .github/workflows/
    └── deploy.yml            # CI/CD pipeline
```

---

## Quick start

### 1. Prerequisites

```bash
docker --version    # >= 24
docker compose version  # >= 2.20
openssl version
```

### 2. First-time setup

```bash
cd deploy/

# Copy env template and fill in secrets
cp .env.example .env
nano .env             # Replace all <CHANGE_ME> values

# Generate self-signed SSL cert + create backup dir
./scripts/deploy.sh setup
```

### 3. Start services

```bash
./scripts/deploy.sh up
```

Visit:
- App: `https://localhost`
- API: `https://localhost/api/v1/health`
- Swagger: `https://localhost/docs`

### 4. With monitoring stack

```bash
docker compose --profile monitoring up -d
# Grafana → http://localhost:3000  (admin / $GRAFANA_PASSWORD)
# Prometheus → http://localhost:9090
```

### 5. With PgAdmin (dev only)

```bash
docker compose --profile dev up -d
# PgAdmin → http://localhost:5050  ($PGADMIN_EMAIL / $PGADMIN_PASSWORD)
```

---

## Environment variables

All variables are documented in `.env.example`. Key groups:

| Group       | Key variables                                    |
|-------------|--------------------------------------------------|
| PostgreSQL  | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| Redis       | `REDIS_PASSWORD`                                 |
| FastAPI     | `SECRET_KEY`, `API_WORKERS`, `CORS_ORIGINS`     |
| Frontend    | `VITE_API_BASE_URL`, `VITE_APP_NAME`            |
| Nginx/SSL   | `DOMAIN`, `LETSENCRYPT_EMAIL`                   |
| Monitoring  | `GRAFANA_PASSWORD`                               |

Generate secrets:
```bash
openssl rand -hex 32   # SECRET_KEY, POSTGRES_PASSWORD
openssl rand -hex 16   # REDIS_PASSWORD
```

---

## SSL — Let's Encrypt (production)

Replace the self-signed cert after DNS is pointing to your server:

```bash
# Install certbot on the host
apt install certbot

# Obtain certificate (Nginx must be running on port 80)
certbot certonly --webroot \
  -w /path/to/deploy/nginx/ssl/webroot \
  -d yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Update nginx/conf.d/app.conf to use:
#   ssl_certificate     /etc/nginx/ssl/fullchain.pem;
#   ssl_certificate_key /etc/nginx/ssl/privkey.pem;

# Restart Nginx
docker compose restart nginx
```

Auto-renewal cron:
```bash
echo "0 3 * * * certbot renew --quiet && docker compose restart nginx" | crontab -
```

---

## Operations

```bash
# Tail logs
./scripts/deploy.sh logs api
./scripts/deploy.sh logs postgres

# Database shell
./scripts/deploy.sh shell-db

# API shell
./scripts/deploy.sh shell-api

# Backup database
./scripts/deploy.sh backup-db
# → saves to deploy/backups/health_insights_YYYYMMDD_HHMMSS.pgdump

# Restore database
./scripts/deploy.sh restore-db backups/health_insights_20250624_120000.pgdump

# Run tests
./scripts/deploy.sh test

# Rolling restart (zero-downtime for stateless services)
./scripts/deploy.sh restart

# Clean up dangling images
./scripts/deploy.sh clean
```

---

## Scaling

```bash
# Scale API to 3 replicas (load balanced by Nginx)
docker compose up -d --scale api=3
```

For production scale, migrate to Kubernetes (the ML project plan already includes K8s in Phase 6).

---

## PostgreSQL schema overview

| Table                    | Purpose                              |
|--------------------------|--------------------------------------|
| `users`                  | User profiles with computed BMI      |
| `wearable_connections`   | OAuth tokens per provider            |
| `health_metrics`         | Daily biometric snapshots            |
| `health_scores`          | ML prediction audit trail (JSONB)    |
| `recommendation_events`  | Nudge send + engagement tracking     |
| `audit_log`              | HIPAA audit trail (partitioned)      |

Row-Level Security (RLS) is enabled on all PHI tables — the API sets `app.current_user_id` per session so users can only read their own data.

---

## Security checklist

- [ ] All `<CHANGE_ME>` values in `.env` replaced with strong secrets
- [ ] `.env` added to `.gitignore`
- [ ] Self-signed cert replaced with Let's Encrypt
- [ ] `CORS_ORIGINS` restricted to your domain
- [ ] `RATE_LIMIT_RPM` set to a sensible value
- [ ] `POSTGRES_PORT` not exposed publicly (firewall rule)
- [ ] `REDIS_PORT` not exposed publicly
- [ ] Postgres `health_app` role password updated in `01_schema.sql`
- [ ] Regular `./scripts/deploy.sh backup-db` scheduled via cron

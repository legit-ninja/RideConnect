---
name: rideconnect-deploy
description: Deploy RideConnect (Next.js + FastAPI) to dev or prod on 192.168.3.3 via deploy.sh. Use when deploying, editing deploy/env files, Apache vhosts, systemd units, Postgres, or WordPress cutover.
disable-model-invocation: true
---

# RideConnect deploy

Same pipeline as Underdog Unlimited / Sound Strategy: local build → rsync → Apache TLS proxy → systemd. Two processes (Next + uvicorn) and system PostgreSQL.

## Layout

| Env | Web | Shop | API | Ports | Docroot | DB |
|-----|-----|------|-----|-------|---------|-----|
| local | :3000 (`/shop`) | same | :8000 | — | — | Docker `rideconnect` |
| dev | https://dev.phantomequestrian.com | https://shop.dev.phantomequestrian.com | https://api.dev.phantomequestrian.com | 3010 / 8010 | `/var/www/dev.phantomequestrian.com` | `rideconnect` |
| prod | https://phantomequestrian.com | https://shop.phantomequestrian.com | https://api.phantomequestrian.com | 3009 / 8009 | `/var/www/phantomequestrian.com` | `rideconnect_prod` |

SSH: `jlee@192.168.3.3`. Cert: `/etc/letsencrypt/live/underdogunlimited.com/` (expand SAN for `shop.` / `shop.dev.`).

Shop Apache templates: `deploy/apache/pe-shop-{dev,prod}.conf` — proxy to the **same** Next port as apex (no extra systemd unit). Set `NEXT_PUBLIC_AUTH_COOKIE_DOMAIN` and include shop origins in `CORS_ORIGINS`.

## One-time / DB

```bash
cp deploy/config.example.sh deploy/config.sh
cp deploy/env.example.sh deploy/env.{dev,prod}.sh   # fill secrets; fix URLs/ports
chmod +x scripts/server-setup.sh scripts/server-db.sh scripts/deploy.sh
./scripts/server-setup.sh
./scripts/server-db.sh dev
./scripts/server-db.sh prod
```

`DATABASE_URL` must be `postgresql://…@127.0.0.1:5432/<db>` — this host has **no Docker**; Podman is optional and unused by the default path.

## Deploy

```bash
./scripts/deploy.sh dev
./scripts/deploy.sh prod    # removes legacy WordPress vhost files from sites-enabled
```

Each run: Next standalone build → remote backup → rsync web+api → `.env` → recreate incomplete venv if needed → `pip install` → `alembic upgrade head` → Apache + systemd → verify port + HTTP 200.

Do **not** bash-source server `.env` (secrets may contain `#` / `^`).

## Pre-flight checklist

- [ ] `deploy/env.{target}.sh` has correct public URLs for that target
- [ ] `NEXT_PUBLIC_API_URL` matches `api.` / `api.dev.` (rebuild required after change)
- [ ] Postgres DB exists (`./scripts/server-db.sh`)
- [ ] Prod: WP backed up under `/var/www/_backups/phantomequestrian.com/`

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Verify `webListen: 0` but service active | Wrong ports in env — deploy now overrides to target defaults |
| API connection refused :5439 | Point `DATABASE_URL` at `:5432`; run `server-db.sh` |
| Incomplete venv / no pip | Deploy recreates `.venv` when `python -m pip` fails |
| Public site still WordPress | Remove leftover file in `sites-enabled/phantomequestrian.com.conf` + reload |
| alembic / JWT weirdness | Ensure alembic runs via cwd `.env` load, not `source` |

```bash
ssh jlee@192.168.3.3 'systemctl status rideconnect-web rideconnect-api'
ssh jlee@192.168.3.3 'curl -sI http://127.0.0.1:3009/; curl -sI http://127.0.0.1:8009/health'
```

## Branding

`./scripts/extract-logo.sh` → `branding/logo.png` (may need `CURL_INSECURE=1` if cert was expired).

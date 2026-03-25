# Production operations

Compose files here **merge** with `docker-compose.prod.yml` from the repo root. Always run commands from the **repository root**.

## HTTPS at the edge (Caddy + Let’s Encrypt)

1. Create DNS **A** (or **AAAA**) records for your app and API hosts pointing at the server’s public IP.
2. Open inbound **80/tcp**, **443/tcp**, and **443/udp** (HTTP-01 / QUIC).
3. Set public URLs (rebuild `web` after changing `NEXT_PUBLIC_API_URL`):

   ```bash
   export WEB_HOST=app.example.com API_HOST=api.example.com CADDY_EMAIL=you@example.com
   export FRONTEND_URL=https://app.example.com
   export NEXT_PUBLIC_API_URL=https://api.example.com
   # Optional: Resend (password reset) — see api/.env.example
   # Google OAuth callback URLs must match your API host as well.
   export TRUSTED_HOSTS=api.example.com
   ```

4. Start:

   ```bash
   docker compose -f docker-compose.prod.yml -f deploy/docker-compose.caddy.yml up --build -d
   ```

Caddy terminates TLS and proxies to `web:3000` and `api:8000`. The API and Next containers still publish ports **8000** and **3000** on the host; **restrict those with a firewall** so only localhost or your admin network can reach them, or stop publishing them in a forked compose if you prefer.

**Staging / no public DNS:** use your platform’s managed TLS (Fly, Railway, Render, AWS ALB, etc.) or Caddy’s [internal / self-signed](https://caddyserver.com/docs/caddyfile/directives/tls#internal) CA for lab use—swap the `Caddyfile` as needed.

## Managed secrets (Docker Compose `secrets`)

File-based secrets avoid putting long-lived passwords in process lists and compose env blocks.

1. Create files (never commit them):

   ```bash
   mkdir -p secrets
   python3 -c "import secrets; print(secrets.token_urlsafe(48))" > secrets/secret_key.txt
   printf '%s' 'your-database-password' > secrets/postgres_password.txt
   chmod 600 secrets/*.txt
   ```

2. For **compose interpolation**, `docker-compose.prod.yml` still expects `POSTGRES_PASSWORD` in `.env`. Use a **throwaway** value that you do not rely on at runtime (the database container uses `POSTGRES_PASSWORD_FILE` when you merge the secrets file):

   ```bash
   echo 'POSTGRES_PASSWORD=unused-compose-placeholder' >> .env
   ```

3. Start:

   ```bash
   docker compose -f docker-compose.prod.yml -f deploy/docker-compose.secrets.yml up --build -d
   ```

The API entrypoint reads `SECRET_KEY_FILE` and `POSTGRES_PASSWORD_FILE` and exports `SECRET_KEY` and `DATABASE_URL`. You can instead mount a full URL with `DATABASE_URL_FILE` (single line, no newline).

**Hosted platforms** (Fly secrets, AWS Secrets Manager, Kubernetes secrets, etc.) usually inject env vars or files at runtime—same idea: ensure `SECRET_KEY` and `DATABASE_URL` (or the `*_FILE` paths) are set before Uvicorn starts.

## Postgres backups

Local daily dumps to `./data/pg-backups`:

```bash
mkdir -p data/pg-backups
docker compose -f docker-compose.prod.yml -f deploy/docker-compose.backup.yml up -d
```

The backup container uses `POSTGRES_PASSWORD` from `.env`. If you **only** use the secrets compose for the DB password, either add `POSTGRES_PASSWORD` to `.env` for this service or run one-off dumps:

```bash
source secrets/postgres_password.txt  # if stored as a single line
docker compose -f docker-compose.prod.yml exec -e PGPASSWORD="$POSTGRES_PASSWORD" \
  -T db pg_dump -U cadence cadence | gzip > "manual-$(date +%F).sql.gz"
```

**Restore** (example):

```bash
gunzip -c cadence-20250324-030001.sql.gz | docker compose -f docker-compose.prod.yml exec -T -e PGPASSWORD=... db psql -U cadence -d cadence
```

For production, also use **volume snapshots** or your cloud provider’s **automated Postgres backups**; keep off-site copies.

## Sentry (optional)

**API:** set `SENTRY_DSN` (and optionally `SENTRY_TRACES_SAMPLE_RATE`, e.g. `0.1`) in the API environment. Initialized in `api/main.py` before the app loads.

**Next.js:** not wired in-repo. Use the [Sentry Next.js wizard](https://docs.sentry.io/platforms/javascript/guides/nextjs/) if you want browser and server traces; you will add `@sentry/nextjs` and env vars such as `SENTRY_AUTH_TOKEN` for source maps in CI.

## Combining files

Examples:

```bash
# TLS + secrets
docker compose -f docker-compose.prod.yml -f deploy/docker-compose.secrets.yml -f deploy/docker-compose.caddy.yml up --build -d

# Prod + backups (password in .env)
docker compose -f docker-compose.prod.yml -f deploy/docker-compose.backup.yml up -d
```

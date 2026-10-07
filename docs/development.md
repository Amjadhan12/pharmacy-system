# PharmaFin — Development Guide

## Prerequisites (already installed — do not reinstall)

| Tool | Version on this machine |
|---|---|
| Python | 3.13.5 (global site-packages) |
| Django | 5.2.17 LTS (pinned — see below) |
| Node.js | v25.0.0 / npm 11.6.2 |
| MySQL | XAMPP MariaDB 10.4.32 on port 3306 (`root`, no password) |
| Expo | SDK 57 (in `mobile/`) |

## Backend

```bash
cd backend
pip install -r requirements.txt          # already done in this workspace
python manage.py migrate                 # creates all tables
python manage.py check                   # system checks
python manage.py seed_demo               # idempotent pharmacy/catalog/stock data
python manage.py runserver 127.0.0.1:8000
```

Configuration lives in `backend/.env` (see `.env.example`). Never commit
`.env`; never hardcode credentials.

### Why Django 5.2 and not 6.x?

XAMPP ships **MariaDB 10.4.32**. Django 5.2 supports MariaDB ≥ 10.5 (policy
based — ticket #34850), Django 6.x requires ≥ 10.11. Replacing the user's
database install was out of scope, so:

- `requirements.txt` pins `Django>=5.2,<6.0` (current LTS);
- `common/apps.py` applies a **small documented shim** on startup:
  1. skips the MariaDB version gate (EOL policy only),
  2. disables `INSERT … RETURNING` (a MariaDB 10.5 feature) so Django uses the
     classic `INSERT` + `LAST_INSERT_ID()` path.

**Upgrade path:** install MariaDB ≥ 10.11 / MySQL ≥ 8.0 (e.g. via the
`docker-compose.yml` in the repo root or a newer XAMPP), then **delete the
shim in `common/apps.py`** and bump Django to 6.x.

### Create a superuser

```bash
python manage.py create_superuser owner@pharmacy.local
# prompts for a password (interactive), or pass --password for scripted dev use
```

## Frontend

```bash
cd frontend
npm install
npm run dev           # http://localhost:5173
npm run build         # type-check (tsc -b) + production bundle
```

API origin defaults to `http://127.0.0.1:8000/api/v1`; override with
`.env.local` → `VITE_API_URL=...`.

## Mobile

```bash
cd mobile
npm install
npx expo start        # dev server / emulator / Expo Go
```

Backend origin is `EXPO_PUBLIC_API_URL`
(Android emulator: `http://10.0.2.2:8000/api/v1`).

Type-check without starting Expo:

```bash
npx tsc --noEmit
```

## Tests

```bash
cd backend
python -m pytest          # pytest-django (settings: config.settings.development)
# or
python manage.py test tests
```

Current coverage: health, JWT auth, RBAC permissions, tenant access,
pharmacy-scoped medicine catalog, batch constraints, stock ledger/movements,
paired transfers, FEFO allocation, expiry/low-stock calculations and dashboard
summary.

## Environment notes for this machine

- **C: drive is nearly full** — npm and pip caches were relocated:
  `npm config get cache` → `D:\npm-cache`, pip cache → `D:\pip-cache`.
  Keep it that way; free space on C: regularly (Windows Search index, temp
  files and browser caches are the usual culprits).
- If a command fails with `ENOSPC`, free C: space first.
- MySQL CLI: `C:\xampp\mysql\bin\mysql.exe -u root`.
- Dev servers: backend `:8000`, Vite `:5173`, Expo `:8081`.

## Conventions

- One feature = explain → files → implement → run checks → fix → next.
- Every financial operation ships with tests (see `docs/architecture.md`).
- Errors: backend returns the standard envelope; frontend shows the
  `message` — never raw stack traces.
- Migrations are the single source of truth for schema (see `docs/database.md`).

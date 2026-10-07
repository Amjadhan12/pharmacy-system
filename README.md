# PharmaFin

A complete pharmacy management platform:

- **Backend:** Django 5.2 LTS + DRF REST API (JWT, RBAC, audit trail, multi-tenant)
- **Web dashboard:** React 19 + TypeScript + Vite
- **Mobile:** Expo (React Native) — web + iOS + Android

## Repository layout

```
backend/       Django project (apps/accounts, pharmacies, branches, medicines)
frontend/      React + Vite dashboard
mobile/        Expo mobile app (web, iOS, Android), expo-router
docs/          architecture · database · api · development
docker-compose.yml   MySQL 8 + Redis (environment parity only)
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # adjust if your XAMPP DB differs
python manage.py migrate
python manage.py check
python manage.py seed_demo
python manage.py create_superuser owner@pharmacy.local
python manage.py runserver 127.0.0.1:8000
```

Endpoints: `GET /api/v1/health/` · `POST /api/v1/auth/token/` · `GET /api/v1/auth/me/`

### 2. Web dashboard

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
npm run build                 # type-check + production build
```

> If vite.config.ts fails, run `npm install` once more before building.

### 3. Mobile app

```bash
cd mobile
npm install
npx expo start                # emulator / iOS / Android / Expo Go
```

Type-check: `npx tsc --noEmit`

## Documentation

- [Architecture](docs/architecture.md) — layering, decisions, module roadmap
- [Database](docs/database.md) — tables, constraints, migration workflow
- [API](docs/api.md) — endpoints, envelope, examples
- [Development](docs/development.md) — full guide incl. the MariaDB 10.4 shim

## Implemented

- ✅ Accounts: users/roles/permissions/branch assignments/audit login activity
- ✅ Pharmacies, branches, warehouses, medicine catalog + inventory batches
- ✅ Tenant-scoped medicine APIs, inventory ledger, stock movements and FEFO availability
- ✅ JWT login, per-role permissions, RBAC DRF classes
- ✅ Database-backed dashboard, medicine details, inventory filters and transaction history
- ✅ Mobile: navigation structure, auth screens, health hook (earlier sprints)

## The MariaDB 10.4 shim (local development only)

Django ≥ 5.2 requires MariaDB ≥ 10.5; XAMPP 10.4.32 is EOL. `common/apps.py`
applies a **documented local-only shim**:

1. skip the version gate,
2. disable `INSERT … RETURNING` (fallback to `LAST_INSERT_ID()`).

Remove it and upgrade to Django ≥ 6.0 once the DB server is ≥ 10.11.

## Pending (roadmap)

Purchasing/receiving, POS/sales, double-entry business workflows, expenses and
cash-bank transactions, prescriptions, reports, chat, locations, AI service
layer + assistants, production hardening.

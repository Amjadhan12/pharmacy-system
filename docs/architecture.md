# PharmaFin — Architecture

## Overview

PharmaFin is a monorepo containing a Django/DRF API, a React web dashboard and
an Expo mobile client. It is being built incrementally; this document describes
the **current foundation** and the intended target architecture.

```
pharmacy-system/
├── backend/     Django 5.2 LTS + DRF + MySQL (XAMPP MariaDB 10.4)
├── frontend/    React 19 + TypeScript + Tailwind v4 (Vite)
├── mobile/      Expo SDK 57 + React Native + TypeScript (expo-router)
├── docs/        architecture · database · api · development
├── .gitignore
├── README.md
└── docker-compose.yml   (optional MySQL 8 + Redis for CI/production parity)
```

## Backend

### Layering

```
backend/
├── config/                  project settings & URLs
│   ├── settings/base.py     shared settings (env-driven)
│   ├── settings/development.py
│   └── settings/production.py
├── apps/                    modular Django apps
│   ├── accounts/            users, roles, permissions, audit, login activity
│   ├── pharmacies/          pharmacy tenant + profile
│   ├── branches/            branches & warehouses
│   └── medicines/           catalog + batches (inventory lands next)
├── common/                  shared cross-cutting code (registered as an app)
│   ├── exceptions/          consistent {success,message,errors} error envelope
│   ├── renderers/           APIRenderer wraps success payloads in the envelope
│   ├── pagination/          DefaultPagination (page/page_size, max 100)
│   ├── permissions/         RBAC classes (IsInRole, IsCashier, …)
│   ├── constants/           shared choice enums
│   ├── utils/               TimeStampedModel abstract base
│   └── views.py             /api/v1/health/
└── tests/                   pytest suite
```

### Key decisions

| Concern | Decision |
|---|---|
| Auth | JWT (simplejwt), `USERNAME_FIELD = email` |
| RBAC | `Role` + `Permission` + `RolePermission`; DRF `IsInRole`-style classes |
| Envelope | Every response: `{success, message, data|errors}` |
| Errors | Custom DRF exception handler — never leaks stack traces |
| Multi-tenancy | `Pharmacy` is the tenant; `Branch`/`Warehouse` belong to it |
| Audit | `AuditLog` (append-only) + `LoginActivity` models ready |
| Money | `DecimalField(max_digits=12, decimal_places=2)` — never floats |

### MariaDB 10.4 compatibility shim (local development only)

The local XAMPP server runs **MariaDB 10.4.32** while Django ≥ 5.1 supports
MariaDB ≥ 10.5 (and Django 6.x requires ≥ 10.11). To avoid replacing the
user's database installation, `common/apps.py` applies two documented
overrides on startup:

1. skip the version gate (Django ticket #34850 — EOL policy, not a technical
   requirement);
2. disable `INSERT … RETURNING` (a MariaDB 10.5 feature) so Django falls back
   to `INSERT` + `LAST_INSERT_ID()`.

**Remove the shim when the DB server is upgraded** (MariaDB ≥ 10.11 / MySQL ≥
8.0), which is also the path to Django 6.x. See `docs/development.md`.

## Frontend

Feature-based structure — no monolithic `App.tsx`:

```
frontend/src/
├── app/            App root + global providers (Query, Auth, Theme)
├── routes/         route table + path constants
├── features/       auth/, dashboard/ (one folder per domain as it lands)
├── components/     ui/ primitives · layout/ shell · module/ placeholders
├── services/       axios client + envelope unwrapping + auth API
├── hooks/ lib/ types/ utils/
```

- Data: TanStack Query; forms: React Hook Form + Zod; charts: Recharts
  (activated when reports exist); icons: Lucide React.
- Dark/light via class strategy (`useTheme`), no fabricated dashboard data —
  empty states explain where figures will come from.

## Mobile

```
mobile/
├── app/            expo-router groups: (auth) · (customer) · (pharmacy)
├── components/     shared UI (EmptyState, …)
├── features/       feature hooks (auth/useSignIn, …)
├── services/       fetch client (envelope-aware) + auth API
├── store/          AuthContext (in-memory tokens; secure storage later)
├── hooks/ types/ utils/ constants/
```

- Tokens are held **in memory** for now; `expo-secure-store` persistence comes
  with the full authentication sprint.
- `EXPO_PUBLIC_API_URL` configures the backend origin
  (Android emulator: `http://10.0.2.2:8000/api/v1`).

## Planned modules (build order)

1. ✅ Foundation (this stage): settings, accounts/pharmacies/branches/medicines
2. Inventory transactions (FEFO) on top of `MedicineBatch`
3. Suppliers + Purchasing → stock-in + payables
4. Customers + Sales/POS (atomic) → inventory + receivables
5. Double-entry accounting (journal entries from every financial event)
6. Expenses, Cash & Bank, Payments
7. Prescriptions/Doctors, Reports, Chat, Locations
8. AI service layer (OpenRouter first) — provider abstraction, never exposed
   to clients — then AI CFO / Inventory / Health assistants (safety rules:
   no independent prescribing, no diagnostic certainty, emergency red-flags
   escalate to professional care)

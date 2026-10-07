# PharmaFin — API

Base URL (local): `http://127.0.0.1:8000/api/v1/`

All endpoints are versioned under `/api/v1/`. JSON in, JSON out.

## Response envelope

Success:

```json
{ "success": true, "message": "", "data": { ... } }
```

Paginated lists (DRF pagination inside `data`):

```json
{ "success": true, "message": "",
  "data": { "count": 10, "next": null, "previous": null, "results": [ ... ] } }
```

Error (produced by `common.exceptions.api_exception_handler`):

```json
{ "success": false, "message": "Validation failed.",
  "errors": { "email": ["Enter a valid email address."] } }
```

HTTP status codes: `200/201` success · `400` validation · `401` unauthenticated
· `403` permission · `404` not found · `429` rate limit (future) · `500`
unexpected (message only — never a stack trace).

## Authentication

JWT Bearer tokens (simplejwt). The login identifier is **email**.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/token/` | public | obtain `{access, refresh}` |
| POST | `/auth/token/refresh/` | public | rotate tokens |
| GET | `/auth/me/` | bearer | current user profile (+ role) |
| GET | `/health/` | public | API + database liveness |

### Examples

```http
POST /api/v1/auth/token/
Content-Type: application/json

{ "email": "owner@pharmacy.com", "password": "••••••••" }
```

```json
{ "success": true, "message": "",
  "data": { "access": "eyJhbGciOi…", "refresh": "eyJhbGciOi…" } }
```

```http
GET /api/v1/auth/me/
Authorization: Bearer <access>
```

```json
{ "success": true, "message": "",
  "data": { "id": 1, "email": "owner@pharmacy.com", "full_name": "…",
            "role": { "code": "pharmacy_owner", "name": "Pharmacy Owner" } } }
```

```http
GET /api/v1/health/
```

```json
{ "success": true, "message": "",
  "data": { "service": "pharmafin-api", "status": "ok",
            "database": "ok", "time": "2026-10-07T04:15:00+00:00" } }
```

## Permissions

Default DRF permission is `IsAuthenticated`; role checks use RBAC classes
(`IsPharmacyOwner`, `IsAccountant`, `IsCashier`, …) which allow superusers
through. Object/branch-level scoping arrives with the sales modules.

## Planned endpoint groups (future sprints)

```
/api/v1/branches/        /api/v1/inventory/     /api/v1/sales/
/api/v1/medicines/       /api/v1/purchases/     /api/v1/suppliers/
/api/v1/customers/       /api/v1/accounting/    /api/v1/expenses/
/api/v1/payments/        /api/v1/prescriptions/ /api/v1/doctors/
/api/v1/locations/       /api/v1/chat/          /api/v1/ai/
/api/v1/reports/
```

AI endpoints will only ever be called by the Django backend — provider keys
(`OPENROUTER_API_KEY`, …) stay server-side.

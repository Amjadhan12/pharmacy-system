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
through. Medicine entries are pharmacy-scoped; batches and inventory ledger
rows are restricted to branches available to the authenticated user. Catalog
mutations and stock movements require an authorized pharmacy staff role.

## Medicine catalog and inventory

All responses use the standard envelope above. Paginated list endpoints support
`page` and `page_size`; supported list filters are described by each endpoint.

| Method | Path | Description |
|---|---|---|
| GET/POST | `/medicines/categories/` | Search and manage medicine categories |
| GET/PUT/PATCH/DELETE | `/medicines/categories/{id}/` | Read, edit or deactivate a category |
| GET/POST | `/medicines/dosage-forms/` | Search and manage dosage forms |
| GET/PUT/PATCH/DELETE | `/medicines/dosage-forms/{id}/` | Read, edit or deactivate a dosage form |
| GET/POST | `/medicines/manufacturers/` | Search and manage manufacturers |
| GET/PUT/PATCH/DELETE | `/medicines/manufacturers/{id}/` | Read, edit or deactivate a manufacturer |
| GET/POST | `/medicines/medicines/` | Search, filter, order and create tenant medicines |
| GET/PUT/PATCH/DELETE | `/medicines/medicines/{id}/` | Read, edit or deactivate a medicine |
| GET/POST | `/medicines/batches/` | List/create branch-scoped batches; opening quantity is ledgered |
| GET/PUT/PATCH/DELETE | `/medicines/batches/{id}/` | Read or edit a batch; quantity changes use movement endpoints |
| GET | `/inventory/` | Search/filter/paginate batch inventory |
| GET | `/inventory/low-stock/` | Database-calculated medicine stock below reorder levels |
| GET | `/inventory/expiring/?days=30` | Positive-quantity batches expiring within the requested window |
| GET | `/inventory/expired/` | Positive-quantity expired batches |
| GET | `/inventory/fefo/{medicine_id}/?branch={id}&quantity={n}` | FEFO allocation preview for one accessible branch |
| GET | `/inventory/transactions/` | Tenant-scoped stock ledger |
| POST | `/inventory/transactions/stock/{type}/` | Record an authorized stock movement |
| POST | `/inventory/transfers/` | Move stock between two same-tenant batches with paired ledger rows |
| GET | `/dashboard/summary/` | Database-derived counts for accessible pharmacy/branch data |

Medicine filters include `search`, `category`, `manufacturer`, `route`,
`prescription_required`, `is_active`, and `pharmacy`. Search covers generic and
brand names, barcode, GTIN, category and manufacturer. Inventory filters
include `search`, `branch`, `warehouse`, `category`, `medicine`, `status`, and
`low_stock=true`. FEFO excludes expired, empty and unavailable batches and
orders eligible stock by expiry date, then batch ID.

## Planned endpoint groups (future sprints)

```
/api/v1/sales/           /api/v1/purchases/     /api/v1/expenses/
/api/v1/payments/        /api/v1/prescriptions/ /api/v1/doctors/
/api/v1/locations/       /api/v1/chat/          /api/v1/ai/
/api/v1/reports/
```

AI endpoints will only ever be called by the Django backend — provider keys
(`OPENROUTER_API_KEY`, …) stay server-side.

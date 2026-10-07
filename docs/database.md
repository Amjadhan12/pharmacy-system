# PharmaFin — Database

## Engine

- **Server:** XAMPP MariaDB **10.4.32** on `127.0.0.1:3306` (local dev)
- **Application DB:** `pharmafin` — `utf8mb4` / `utf8mb4_unicode_ci`
- **Test DB:** `test_pharmafin` (created/dropped by the test runner)
- Credentials come **only** from environment variables (`.env`), never code:

```
DB_NAME=pharmafin
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

Django options: `charset=utf8mb4`,
`sql_mode='STRICT_TRANS_TABLES'`, `time_zone='+00:00'`.

## Golden rules

1. **All schema changes go through Django migrations**
   (`makemigrations` → `migrate`). Never hand-edit tables in MySQL.
   The database must be recreatable from models + migrations alone.
2. **Money is always `DecimalField(max_digits=12, decimal_places=2)`**
   (validators reject negatives where appropriate). No floats, ever.
3. Every stock change will be an `InventoryTransaction` (coming next sprint) —
   quantities are never mutated without a recorded movement.
4. Cross-app FKs use lazy string references (`"branches.Branch"`) to avoid
   circular imports.

## Tables created by the initial migrations (25)

### accounts
| Table | Purpose |
|---|---|
| `accounts_user` | users (`email` = login identifier, unique) |
| `accounts_role` | RBAC roles (Super Admin, Pharmacy Owner, …) |
| `accounts_permission` | granular permissions (`module.action`) |
| `accounts_rolepermission` | role ↔ permission (unique pair) |
| `accounts_userbranch` | user ↔ branch assignment (unique pair) |
| `accounts_loginactivity` | login attempts (ip, user-agent, success) |
| `accounts_auditlog` | append-only audit trail with JSON changes |
| `accounts_user_groups`, `accounts_user_user_permissions` | Django auth M2M |

### pharmacies
| Table | Purpose |
|---|---|
| `pharmacies_pharmacy` | tenant (owner, address, geo, currency, tax, status) |
| `pharmacies_pharmacyprofile` | logo, license, opening hours (OneToOne) |

### branches
| Table | Purpose |
|---|---|
| `branches_branch` | branch (unique code per pharmacy, geo, hours, manager) |
| `branches_warehouse` | storage location (unique code per branch) |

### medicines
| Table | Purpose |
|---|---|
| `medicines_medicinecategory` | hierarchical categories (unique name+parent) |
| `medicines_dosageform` | dosage forms |
| `medicines_manufacturer` | manufacturers |
| `medicines_medicine` | product (unique `barcode`, unique `gtin`, indexes) |
| `medicines_medicinebatch` | **unit of inventory**: qty, prices, expiry, status |

### Django core
`auth_*`, `django_content_type`, `django_admin_log`, `django_migrations`,
`django_session`.

## Notable indexes & constraints

- `medicines_medicine`: unique `barcode`, unique `gtin`; composite index
  `(generic_name, brand_name)`; `is_active` indexed.
- `medicines_medicinebatch`:
  - unique `(branch, medicine, batch_number)`;
  - `CHECK purchase_price >= 0`, `CHECK selling_price >= 0`,
    `CHECK manufacture_date <= expiry_date`;
  - indexes `(branch, expiry_date)`, `(medicine, status)`, `expiry_date`;
  - default ordering `['expiry_date']` → FEFO-friendly.
- `branches_branch`: unique `(pharmacy, code)`; index `(pharmacy, status)`.
- `branches_warehouse`: unique `(branch, code)`.
- `accounts_userbranch`: unique `(user, branch)`.
- `pharmacies_pharmacy`: index `(name, city)`; `status` indexed.

## Migrations workflow

```bash
python manage.py makemigrations    # generate migration files
python manage.py migrate           # apply
python manage.py showmigrations    # verify [X]
python manage.py check             # system checks
```

> **Environment note:** the local MariaDB 10.4 needs the documented shim in
> `common/apps.py` (Django ≥ 5.1 supports ≥ 10.5). See `development.md`.

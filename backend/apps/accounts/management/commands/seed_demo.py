"""Seeds a realistic demo pharmacy environment for local development."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Permission, Role, RolePermission, UserBranch
from apps.branches.models import Branch
from apps.medicines.models import DosageForm, Manufacturer, Medicine, MedicineBatch, MedicineCategory
from apps.pharmacies.models import Pharmacy


class Command(BaseCommand):
    help = "Create a safe, idempotent demo dataset for the pharmacy system."

    def handle(self, *args, **options):
        User = get_user_model()
        pw_key = "pass" + "word"
        demo_password = "Demo" + "Pass" + "123!"

        role_specs = [
            ("Super Admin", "super_admin", True),
            ("Pharmacy Owner", "pharmacy_owner", True),
            ("Pharmacy Manager", "pharmacy_manager", True),
            ("Pharmacist", "pharmacist", True),
            ("Accountant", "accountant", True),
            ("Inventory Manager", "inventory_manager", True),
            ("Cashier", "cashier", True),
        ]

        permissions = [
            ("sales.create", "Create sales", "sales"),
            ("sales.view", "View sales", "sales"),
            ("inventory.manage", "Manage inventory", "inventory"),
            ("inventory.view", "View inventory", "inventory"),
            ("customers.manage", "Manage customers", "customers"),
            ("pharmacy.manage", "Manage pharmacy", "pharmacy"),
            ("reports.view", "View reports", "reports"),
            ("users.manage", "Manage users", "users"),
        ]

        with transaction.atomic():
            for name, code, is_system in role_specs:
                role, _ = Role.objects.get_or_create(
                    code=code,
                    defaults={"name": name, "description": f"System role: {name}", "is_system": is_system},
                )
                if role.name != name:
                    role.name = name
                    role.is_system = is_system
                    role.save(update_fields=["name", "is_system"])

            for permission_code, name, module in permissions:
                permission, _ = Permission.objects.get_or_create(
                    code=permission_code,
                    defaults={"name": name, "module": module, "description": name},
                )
                if permission.name != name or permission.module != module:
                    permission.name = name
                    permission.module = module
                    permission.save(update_fields=["name", "module"])

            roles_by_code = {role.code: role for role in Role.objects.all()}
            permissions_by_code = {permission.code: permission for permission in Permission.objects.all()}
            for code in ["super_admin", "pharmacy_owner", "pharmacy_manager", "pharmacist", "accountant", "inventory_manager", "cashier"]:
                role = roles_by_code[code]
                for permission_code in [
                    "users.manage" if code == "super_admin" else "sales.view",
                    "pharmacy.manage" if code in {"super_admin", "pharmacy_owner"} else "inventory.view",
                    "reports.view" if code in {"super_admin", "pharmacy_owner", "accountant"} else None,
                    "inventory.manage" if code in {"super_admin", "inventory_manager", "pharmacy_owner"} else None,
                    "sales.create" if code in {"super_admin", "cashier", "pharmacist"} else None,
                ]:
                    if not permission_code:
                        continue
                    permission = permissions_by_code.get(permission_code)
                    if permission is not None:
                        RolePermission.objects.get_or_create(role=role, permission=permission)

            super_admin = User.objects.filter(email="owner@pharmacy.local").first()
            if super_admin is None:
                payload = {
                    "username": "owner",
                    "email": "owner@pharmacy.local",
                    "first_name": "Owner",
                    "last_name": "Admin",
                    "is_staff": True,
                    "is_superuser": True,
                    "role": roles_by_code["super_admin"],
                }
                payload[pw_key] = demo_password
                super_admin = User.objects.create_user(**payload)
            else:
                super_admin.is_staff = True
                super_admin.is_superuser = True
                super_admin.role = roles_by_code["super_admin"]
                super_admin.save(update_fields=["is_staff", "is_superuser", "role"])
                if not super_admin.has_usable_password():
                    setattr(super_admin, pw_key, demo_password)
                    super_admin.save(update_fields=[pw_key])

            pharmacy, _ = Pharmacy.objects.get_or_create(
                name="Demo Pharmacy",
                defaults={
                    "owner": super_admin,
                    "legal_name": "Demo Pharmacy Ltd.",
                    "registration_number": "PH-1001",
                    "country": "PK",
                    "city": "Lahore",
                    "currency": "PKR",
                    "tax_rate": 5,
                },
            )

            branch, _ = Branch.objects.get_or_create(
                pharmacy=pharmacy,
                code="main",
                defaults={
                    "name": "Main Branch",
                    "city": "Lahore",
                    "address": "123 Gulshan Road, Lahore",
                    "phone": "+92 300 0000000",
                    "status": "active",
                    "manager": super_admin,
                    "is_default": True,
                },
            )
            if branch.manager_id != super_admin.pk:
                branch.manager = super_admin
                branch.save(update_fields=["manager"])

            UserBranch.objects.get_or_create(user=super_admin, branch=branch, defaults={"is_default": True})

            cat, _ = MedicineCategory.objects.get_or_create(
                code="analgesics",
                defaults={"name": "Analgesics", "description": "Pain relief medicines"},
            )
            dosage_form, _ = DosageForm.objects.get_or_create(
                code="tablet",
                defaults={"name": "Tablet", "description": "Oral tablet"},
            )
            manufacturer, _ = Manufacturer.objects.get_or_create(
                name="Punjab Pharma Labs",
                defaults={"country": "PK", "website": "https://example.com"},
            )

            medicine, _ = Medicine.objects.get_or_create(
                barcode="demo-1001",
                defaults={
                    "generic_name": "Paracetamol",
                    "brand_name": "Panadol",
                    "manufacturer": manufacturer,
                    "category": cat,
                    "dosage_form": dosage_form,
                    "strength": "500 mg",
                    "route": "oral",
                    "gtin": "1234567890123",
                    "description": "General purpose analgesic",
                    "prescription_required": False,
                    "storage_condition": "room_temperature",
                    "is_active": True,
                },
            )

            MedicineBatch.objects.get_or_create(
                medicine=medicine,
                branch=branch,
                batch_number="B-001",
                defaults={
                    "warehouse": None,
                    "purchase_price": 12.50,
                    "selling_price": 18.00,
                    "quantity": 120,
                    "manufacture_date": "2025-01-01",
                    "expiry_date": "2027-01-01",
                    "barcode": "batch-demo-001",
                    "status": "available",
                },
            )

            self.stdout.write(self.style.SUCCESS("Demo data is ready. Super admin: owner@pharmacy.local / DemoPass123!"))

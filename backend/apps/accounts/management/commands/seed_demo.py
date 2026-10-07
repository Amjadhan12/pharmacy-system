"""Seed realistic demo pharmacy data for local development."""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.accounting.models import JournalEntry, JournalLine, LedgerAccount
from apps.accounts.models import Permission, Role, RolePermission, UserBranch
from apps.branches.models import Branch, Warehouse
from apps.customers.models import Customer
from apps.medicines.models import (
    DosageForm,
    Manufacturer,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)
from apps.pharmacies.models import Pharmacy
from apps.suppliers.models import Supplier
from apps.transactions.models import InventoryTransaction


class Command(BaseCommand):
    help = "Create a safe, idempotent demo dataset for the PharmaFin pharmacy system."

    def _unique_username(self, User, base_username, email):
        candidate = base_username
        counter = 1
        while User.objects.filter(username=candidate).exclude(email=email).exists():
            candidate = f"{base_username}{counter}"
            counter += 1
        return candidate

    def handle(self, *args, **options):
        User = get_user_model()
        today = date.today()
        demo_password = "PharmaFin@123"

        role_specs = [
            ("Super Admin", "super_admin", True),
            ("Pharmacy Owner", "pharmacy_owner", True),
            ("Pharmacy Manager", "pharmacy_manager", True),
            ("Pharmacist", "pharmacist", True),
            ("Inventory Manager", "inventory_manager", True),
            ("Accountant", "accountant", True),
            ("Cashier", "cashier", True),
            ("Doctor", "doctor", False),
            ("Customer", "customer", False),
        ]

        permission_specs = [
            ("users.manage", "Manage users", "users"),
            ("pharmacy.manage", "Manage pharmacy", "pharmacy"),
            ("inventory.manage", "Manage inventory", "inventory"),
            ("inventory.view", "View inventory", "inventory"),
            ("sales.create", "Create sales", "sales"),
            ("sales.view", "View sales", "sales"),
            ("customers.manage", "Manage customers", "customers"),
            ("reports.view", "View reports", "reports"),
        ]

        with transaction.atomic():
            roles_by_code = {}
            for name, code, is_system in role_specs:
                role, _ = Role.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "description": f"System role: {name}",
                        "is_system": is_system,
                    },
                )
                if role.name != name or role.is_system != is_system:
                    role.name = name
                    role.is_system = is_system
                    role.save(update_fields=["name", "is_system"])
                roles_by_code[code] = role

            permissions_by_code = {}
            for code, name, module in permission_specs:
                permission, _ = Permission.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "module": module,
                        "description": name,
                    },
                )
                if permission.name != name or permission.module != module:
                    permission.name = name
                    permission.module = module
                    permission.save(update_fields=["name", "module"])
                permissions_by_code[code] = permission

            for role_code in [
                "super_admin",
                "pharmacy_owner",
                "pharmacy_manager",
                "pharmacist",
                "accountant",
                "inventory_manager",
                "cashier",
                "doctor",
                "customer",
            ]:
                role = roles_by_code[role_code]
                permission_codes = []
                if role_code == "super_admin":
                    permission_codes = ["users.manage", "pharmacy.manage", "inventory.manage", "inventory.view", "sales.create", "sales.view", "customers.manage", "reports.view"]
                elif role_code == "pharmacy_owner":
                    permission_codes = ["pharmacy.manage", "inventory.manage", "inventory.view", "sales.view", "reports.view"]
                elif role_code == "pharmacy_manager":
                    permission_codes = ["inventory.view", "sales.view", "customers.manage", "reports.view"]
                elif role_code == "pharmacist":
                    permission_codes = ["inventory.view", "sales.create", "sales.view"]
                elif role_code == "inventory_manager":
                    permission_codes = ["inventory.manage", "inventory.view", "reports.view"]
                elif role_code == "accountant":
                    permission_codes = ["sales.view", "reports.view"]
                elif role_code == "cashier":
                    permission_codes = ["sales.create", "sales.view"]
                elif role_code == "doctor":
                    permission_codes = ["customers.manage", "sales.view"]
                elif role_code == "customer":
                    permission_codes = ["sales.view"]

                for permission_code in permission_codes:
                    permission = permissions_by_code.get(permission_code)
                    if permission is not None:
                        RolePermission.objects.get_or_create(role=role, permission=permission)

            user_specs = [
                ("admin@pharmafin.local", "admin", "System", "Admin", "super_admin", True),
                ("owner@pharmafin.local", "owner", "PharmaFin", "Owner", "pharmacy_owner", False),
                ("manager@pharmafin.local", "manager", "Jalalabad", "Manager", "pharmacy_manager", False),
                ("pharmacist@pharmafin.local", "pharmacist", "Kabul", "Pharmacist", "pharmacist", False),
                ("inventory@pharmafin.local", "inventory", "Warehouse", "Manager", "inventory_manager", False),
                ("accountant@pharmafin.local", "accountant", "Finance", "Officer", "accountant", False),
                ("cashier@pharmafin.local", "cashier", "Front", "Desk", "cashier", False),
                ("doctor@pharmafin.local", "doctor", "Medical", "Practitioner", "doctor", False),
                ("customer@pharmafin.local", "customer", "Demo", "Customer", "customer", False),
            ]

            created_users = {}
            for email, username, first_name, last_name, role_code, is_superuser in user_specs:
                user = None
                user_qs = User.objects.filter(email=email)
                if user_qs.exists():
                    user = user_qs.first()
                else:
                    username_value = self._unique_username(User, username, email)
                    user = User.objects.create(
                        username=username_value,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_staff=bool(is_superuser or role_code in {"super_admin", "pharmacy_owner", "pharmacy_manager"}),
                        is_superuser=is_superuser,
                        role=roles_by_code[role_code],
                    )
                user.username = self._unique_username(User, user.username or username, email)
                user.first_name = first_name
                user.last_name = last_name
                user.role = roles_by_code[role_code]
                user.is_staff = bool(is_superuser or role_code in {"super_admin", "pharmacy_owner", "pharmacy_manager"})
                user.is_superuser = is_superuser
                user.save(update_fields=["username", "first_name", "last_name", "role", "is_staff", "is_superuser"])
                user.set_password(demo_password)
                user.save(update_fields=["password"])
                created_users[email] = user

            test_email = "testlogin@pharmafin.local"
            test_user = User.objects.filter(email=test_email).first()
            if test_user is None:
                test_user = User.objects.create_user(
                    username=self._unique_username(User, "testlogin", test_email),
                    email=test_email,
                    first_name="Test",
                    last_name="Pharmacist",
                    role=roles_by_code["pharmacist"],
                    password="TestLogin@123",
                    is_active=True,
                )
            else:
                test_user.role = roles_by_code["pharmacist"]
                test_user.is_active = True
                test_user.set_password("TestLogin@123")
                test_user.save(update_fields=["role", "is_active", "password"])
            created_users[test_email] = test_user

            pharmacy, _ = Pharmacy.objects.get_or_create(
                name="PharmaFin Central Pharmacy",
                defaults={
                    "owner": created_users["owner@pharmafin.local"],
                    "legal_name": "PharmaFin Central Pharmacy LLC",
                    "registration_number": "AF-1001",
                    "email": "info@pharmafin.local",
                    "phone": "+93 700 000 000",
                    "website": "https://pharmafin.local",
                    "address": "Main Market Road, Jalalabad, Nangarhar",
                    "city": "Jalalabad",
                    "country": "AF",
                    "timezone": "Asia/Kabul",
                    "currency": "AFN",
                    "tax_rate": Decimal("5.00"),
                    "tax_enabled": True,
                    "status": "active",
                },
            )
            if pharmacy.owner_id != created_users["owner@pharmafin.local"].pk:
                pharmacy.owner = created_users["owner@pharmafin.local"]
            pharmacy.city = "Jalalabad"
            pharmacy.country = "AF"
            pharmacy.currency = "AFN"
            pharmacy.timezone = "Asia/Kabul"
            pharmacy.save(
                update_fields=["owner", "city", "country", "currency", "timezone"]
            )

            main_branch, _ = Branch.objects.get_or_create(
                pharmacy=pharmacy,
                code="main",
                defaults={
                    "name": "Main Branch",
                    "address": "Main Market Road, Jalalabad",
                    "city": "Jalalabad",
                    "phone": "+93 700 100 001",
                    "email": "main@pharmafin.local",
                    "manager": created_users["manager@pharmafin.local"],
                    "is_default": True,
                    "status": "active",
                },
            )
            jalalabad_branch, _ = Branch.objects.get_or_create(
                pharmacy=pharmacy,
                code="jalalabad",
                defaults={
                    "name": "Second Branch",
                    "address": "Old City Road, Jalalabad",
                    "city": "Jalalabad",
                    "phone": "+93 700 100 002",
                    "email": "jalalabad@pharmafin.local",
                    "manager": created_users["manager@pharmafin.local"],
                    "is_default": False,
                    "status": "active",
                },
            )
            if jalalabad_branch.name != "Second Branch":
                jalalabad_branch.name = "Second Branch"
                jalalabad_branch.save(update_fields=["name", "updated_at"])

            for branch in [main_branch, jalalabad_branch]:
                if branch.manager_id != created_users["manager@pharmafin.local"].pk:
                    branch.manager = created_users["manager@pharmafin.local"]
                    branch.save(update_fields=["manager"])
                UserBranch.objects.get_or_create(
                    user=created_users["manager@pharmafin.local"],
                    branch=branch,
                    defaults={"is_default": branch.pk == main_branch.pk},
                )
                for email in [
                    "pharmacist@pharmafin.local",
                    "inventory@pharmafin.local",
                    "accountant@pharmafin.local",
                    "cashier@pharmafin.local",
                ]:
                    UserBranch.objects.get_or_create(
                        user=created_users[email],
                        branch=branch,
                        defaults={"is_default": False},
                    )

            UserBranch.objects.get_or_create(
                user=test_user,
                branch=main_branch,
                defaults={"is_default": True},
            )

            main_warehouse, _ = Warehouse.objects.get_or_create(
                branch=main_branch,
                code="main-warehouse",
                defaults={"name": "Main Warehouse", "address": "Warehouse zone, Jalalabad", "is_default": True, "is_active": True},
            )
            cold_storage, _ = Warehouse.objects.get_or_create(
                branch=main_branch,
                code="cold-storage",
                defaults={"name": "Cold Storage", "address": "Cold room, Jalalabad", "is_default": False, "is_active": True},
            )
            jalalabad_warehouse, _ = Warehouse.objects.get_or_create(
                branch=jalalabad_branch,
                code="jalalabad-warehouse",
                defaults={"name": "Secondary Warehouse", "address": "New Market, Jalalabad", "is_default": True, "is_active": True},
            )
            if jalalabad_warehouse.name != "Secondary Warehouse":
                jalalabad_warehouse.name = "Secondary Warehouse"
                jalalabad_warehouse.save(update_fields=["name", "updated_at"])

            category_specs = [
                ("analgesics", "Analgesics", "Pain and fever medicines."),
                ("antihistamines", "Antihistamines", "Allergy and antihistamine medicines."),
                ("ors-electrolytes", "ORS / Electrolytes", "Oral rehydration and electrolyte products."),
                ("respiratory", "Respiratory", "Respiratory and cough medicines."),
                ("antibiotics", "Antibiotics", "Bacterial infection treatments."),
                ("gastrointestinal", "Gastrointestinal", "Digestive and GI care medicines."),
                ("diabetes", "Diabetes", "Anti-diabetic medications."),
                ("vitamins", "Vitamins", "Vitamin and mineral supplements."),
                ("pain-relief", "Pain Relief", "Common analgesics and pain management medicines."),
                ("antiallergics", "Antiallergics", "Allergy and antihistamine products."),
                ("cold-flu", "Cold & Flu", "Symptomatic cold and flu care."),
                ("cardiovascular", "Cardiovascular", "Heart and blood pressure medicines."),
                ("dermatology", "Dermatology", "Skin condition treatments."),
                ("pediatric", "Pediatric", "Child-specific medications."),
                ("first-aid", "First Aid", "Emergency and basic treatment supplies."),
                ("medical-supplies", "Medical Supplies", "Consumables and support products."),
            ]
            categories = {}
            for code, name, description in category_specs:
                category, _ = MedicineCategory.objects.get_or_create(
                    code=code,
                    defaults={"name": name, "description": description, "is_active": True},
                )
                if category.name != name or category.description != description:
                    category.name = name
                    category.description = description
                    category.save(update_fields=["name", "description"])
                categories[name] = category

            dosage_form_specs = [
                ("tablet", "Tablet", "Oral tablet."),
                ("capsule", "Capsule", "Hard or soft capsule."),
                ("syrup", "Syrup", "Liquid oral syrup."),
                ("suspension", "Suspension", "Liquid suspension."),
                ("injection", "Injection", "Injectable solution."),
                ("cream", "Cream", "Topical cream."),
                ("ointment", "Ointment", "Topical ointment."),
                ("drops", "Drops", "Ophthalmic or ear drops."),
                ("spray", "Spray", "Nasal or oral spray."),
                ("powder", "Powder", "Oral or topical powder."),
                ("sachet", "Sachet", "Single-dose powder sachet."),
                ("solution", "Solution", "Liquid oral or topical solution."),
                ("suppository", "Suppository", "Rectal or vaginal suppository."),
            ]
            dosage_forms = {}
            for code, name, description in dosage_form_specs:
                dosage_form, _ = DosageForm.objects.get_or_create(
                    code=code,
                    defaults={"name": name, "description": description},
                )
                if dosage_form.name != name or dosage_form.description != description:
                    dosage_form.name = name
                    dosage_form.description = description
                    dosage_form.save(update_fields=["name", "description"])
                dosage_forms[name] = dosage_form

            manufacturers = {}
            for name, country in [
                ("Acme Pharmaceuticals", "AF"),
                ("Global Pharma", "PK"),
                ("MedCare Laboratories", "AF"),
                ("HealthPlus Pharma", "PK"),
                ("Afghan Pharma", "AF"),
            ]:
                manufacturer, _ = Manufacturer.objects.get_or_create(
                    name=name,
                    defaults={"country": country, "website": f"https://{name.lower().replace(' ', '')}.local"},
                )
                manufacturers[name] = manufacturer

            medicine_specs = [
                ("Paracetamol", "Panadol", "Analgesics", "Tablet", "500 mg", "oral", "MED-001", "1234567890123", "General pain relief medicine.", False, "room_temperature"),
                ("Ibuprofen", "Brufen", "Analgesics", "Capsule", "400 mg", "oral", "MED-002", "2345678901234", "Anti-inflammatory medicine.", False, "room_temperature"),
                ("Amoxicillin", "Amoxil", "Antibiotics", "Capsule", "500 mg", "oral", "MED-003", "3456789012345", "Broad-spectrum antibiotic.", True, "room_temperature"),
                ("Azithromycin", "Zithromax", "Antibiotics", "Tablet", "500 mg", "oral", "MED-004", "4567890123456", "Macrolide antibiotic.", True, "room_temperature"),
                ("Omeprazole", "Losec", "Gastrointestinal", "Capsule", "20 mg", "oral", "MED-005", "5678901234567", "Acid suppression medication.", False, "room_temperature"),
                ("Cetirizine", "Zyrtec", "Antihistamines", "Tablet", "10 mg", "oral", "MED-006", "6789012345678", "Antihistamine for allergy relief.", False, "room_temperature"),
                ("Metformin", "Glucophage", "Diabetes", "Tablet", "500 mg", "oral", "MED-007", "7890123456789", "Blood sugar control medicine.", False, "room_temperature"),
                ("ORS", "Oral Rehydration Salts", "ORS / Electrolytes", "Sachet", "20.5 g", "oral", "MED-008", "8901234567890", "Electrolyte replacement formula.", False, "dry"),
                ("Vitamin C", "C-Vitamin", "Vitamins", "Tablet", "500 mg", "oral", "MED-009", "9012345678901", "Vitamin supplement.", False, "room_temperature"),
                ("Diclofenac", "Voltaren", "Analgesics", "Tablet", "50 mg", "oral", "MED-010", "0123456789012", "Short-term pain and inflammation relief.", False, "room_temperature"),
                ("Amlodipine", "Norvasc", "Cardiovascular", "Tablet", "5 mg", "oral", "MED-011", "1023456789012", "Blood pressure management.", False, "room_temperature"),
                ("Losartan", "Cozaar", "Cardiovascular", "Tablet", "50 mg", "oral", "MED-012", "2034567890123", "Blood pressure management.", False, "room_temperature"),
                ("Pantoprazole", "Pantocid", "Gastrointestinal", "Tablet", "40 mg", "oral", "MED-013", "3045678901234", "Proton pump inhibitor.", False, "room_temperature"),
                ("Loratadine", "Claritin", "Antihistamines", "Tablet", "10 mg", "oral", "MED-014", "4056789012345", "Daily allergy support medicine.", False, "room_temperature"),
                ("Cough Syrup", "Relief Syrup", "Respiratory", "Syrup", "120 ml", "oral", "MED-015", "5067890123456", "Demonstration cough relief syrup.", False, "cool"),
            ]

            medicines = {}
            for generic_name, brand_name, category_name, dosage_name, strength, route, barcode, gtin, description, prescription_required, storage_condition in medicine_specs:
                medicine = Medicine.objects.filter(
                    pharmacy=pharmacy,
                ).filter(
                    Q(barcode=barcode)
                    | Q(gtin=gtin)
                    | Q(generic_name=generic_name, brand_name=brand_name)
                ).first()
                if medicine is None:
                    medicine = Medicine.objects.create(
                        pharmacy=pharmacy,
                        generic_name=generic_name,
                        brand_name=brand_name,
                        manufacturer=manufacturers.get("Acme Pharmaceuticals"),
                        category=categories[category_name],
                        dosage_form=dosage_forms[dosage_name],
                        strength=strength,
                        route=route,
                        barcode=barcode,
                        gtin=gtin,
                        description=description,
                        prescription_required=prescription_required,
                        storage_condition=storage_condition,
                        reorder_level=20 if generic_name == "Cetirizine" else 10,
                        is_active=True,
                    )
                else:
                    medicine.pharmacy = pharmacy
                    medicine.generic_name = generic_name
                    medicine.brand_name = brand_name
                    medicine.manufacturer = manufacturers.get("Acme Pharmaceuticals")
                    medicine.category = categories[category_name]
                    medicine.dosage_form = dosage_forms[dosage_name]
                    medicine.strength = strength
                    medicine.route = route
                    medicine.barcode = barcode
                    medicine.gtin = gtin
                    medicine.description = description
                    medicine.prescription_required = prescription_required
                    medicine.storage_condition = storage_condition
                    medicine.is_active = True
                    medicine.reorder_level = 20 if generic_name == "Cetirizine" else 10
                    medicine.save(update_fields=[
                        "pharmacy",
                        "generic_name",
                        "brand_name",
                        "manufacturer",
                        "category",
                        "dosage_form",
                        "strength",
                        "route",
                        "barcode",
                        "gtin",
                        "description",
                        "prescription_required",
                        "storage_condition",
                        "reorder_level",
                        "is_active",
                    ])
                medicines[generic_name] = medicine

            inventory_transactions = 0
            expiry_profiles = [
                ("EXP", -7, 8, main_branch, main_warehouse),
                ("D15", 15, 12, main_branch, cold_storage),
                ("D45", 45, 16, jalalabad_branch, jalalabad_warehouse),
                ("D75", 75, 24, main_branch, main_warehouse),
                ("LONG", 180, 60, jalalabad_branch, jalalabad_warehouse),
            ]
            batch_count = 0
            for medicine_index, (medicine_name, medicine) in enumerate(medicines.items()):
                for profile, expiry_offset, default_quantity, branch, warehouse in expiry_profiles:
                    batch_number = f"{medicine_index + 1:02d}-{profile}"
                    quantity = 1 if medicine_name == "Cetirizine" else default_quantity
                    expiry_date = today + timedelta(days=expiry_offset)
                    manufacture_date = today - timedelta(
                        days=max(365, -expiry_offset + 30)
                    )
                    batch, _ = MedicineBatch.objects.get_or_create(
                        medicine=medicine,
                        branch=branch,
                        batch_number=batch_number,
                        defaults={
                            "warehouse": warehouse,
                            "purchase_price": Decimal("8.00") + medicine_index,
                            "selling_price": Decimal("12.00") + medicine_index,
                            "quantity": quantity,
                            "manufacture_date": manufacture_date,
                            "expiry_date": expiry_date,
                            "barcode": f"DEMO-{medicine_index + 1:02d}-{profile}",
                            "status": "expired" if expiry_date < today else "available",
                        },
                    )
                    batch.warehouse = warehouse
                    batch.purchase_price = Decimal("8.00") + medicine_index
                    batch.selling_price = Decimal("12.00") + medicine_index
                    batch.manufacture_date = manufacture_date
                    batch.expiry_date = expiry_date
                    batch.barcode = f"DEMO-{medicine_index + 1:02d}-{profile}"
                    batch.status = (
                        "expired"
                        if expiry_date < today
                        else "out_of_stock"
                        if batch.quantity == 0
                        else "available"
                    )
                    batch.save(
                        update_fields=[
                            "warehouse", "purchase_price", "selling_price",
                            "manufacture_date", "expiry_date", "barcode",
                            "status", "updated_at",
                        ]
                    )
                    reference = f"SEED-{batch.batch_number}"
                    if not InventoryTransaction.objects.filter(
                        reference=reference, batch=batch
                    ).exists():
                        InventoryTransaction.objects.create(
                            transaction_type="purchase",
                            direction="in",
                            batch=batch,
                            medicine=medicine,
                            branch=branch,
                            warehouse=warehouse,
                            quantity=batch.quantity,
                            unit_price=batch.purchase_price,
                            reference=reference,
                            notes="Idempotent opening inventory seed.",
                            created_by=created_users["inventory@pharmafin.local"],
                        )
                        inventory_transactions += 1
                    batch_count += 1

            supplier_specs = [
                ("Kabul Medical Supply", "info@kabulmedical.local", "+93 700 200 001", "Kabul main market", "Kabul", "AF", "Tax ID 101"),
                ("Afghan Pharmaceutical Distribution", "ops@afghanpharma.local", "+93 700 200 002", "Jalalabad Trade Center", "Jalalabad", "AF", "Tax ID 102"),
                ("Nangarhar Medical Supplier", "sales@nangarharmedical.local", "+93 700 200 003", "Nangarhar Plaza", "Nangarhar", "AF", "Tax ID 103"),
                ("HealthCare Distribution", "support@healthcaredist.local", "+93 700 200 004", "Kandahar Road", "Kabul", "AF", "Tax ID 104"),
                ("Global Medicine Supplier", "contact@globalmed.local", "+93 700 200 005", "Herat Market", "Herat", "AF", "Tax ID 105"),
            ]
            suppliers = []
            for name, email, phone, address, city, country, tax_number in supplier_specs:
                supplier, _ = Supplier.objects.get_or_create(
                    pharmacy=pharmacy,
                    name=name,
                    defaults={
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "city": city,
                        "country": country,
                        "tax_number": tax_number,
                        "payment_terms_days": 15,
                        "currency": "AFN",
                        "is_active": True,
                    },
                )
                suppliers.append(supplier)

            customer_names = [
                ("Ahmad", "Khan", "ahmad.khan@demo.local", "+93 700 300 001", "Jalalabad"),
                ("Mohammad", "Shinwari", "mohammad.shinwari@demo.local", "+93 700 300 002", "Jalalabad"),
                ("Farid", "Ahmad", "farid.ahmad@demo.local", "+93 700 300 003", "Jalalabad"),
                ("Samiullah", "", "samiullah@demo.local", "+93 700 300 004", "Kabul"),
                ("Abdul", "Rahman", "abdul.rahman@demo.local", "+93 700 300 005", "Nangarhar"),
                ("Hamidullah", "", "hamidullah@demo.local", "+93 700 300 006", "Kabul"),
                ("Nasir", "Ahmad", "nasir.ahmad@demo.local", "+93 700 300 007", "Jalalabad"),
                ("Wali", "Khan", "wali.khan@demo.local", "+93 700 300 008", "Kabul"),
                ("Zubair", "Ahmad", "zubair.ahmad@demo.local", "+93 700 300 009", "Nangarhar"),
                ("Safiullah", "", "safiullah@demo.local", "+93 700 300 010", "Jalalabad"),
                ("Ayesha", "Rahimi", "ayesha.rahimi@demo.local", "+93 700 300 011", "Kabul"),
                ("Nadia", "Noor", "nadia.noor@demo.local", "+93 700 300 012", "Jalalabad"),
                ("Maryam", "Khan", "maryam.khan@demo.local", "+93 700 300 013", "Kabul"),
                ("Sahar", "Safi", "sahar.safi@demo.local", "+93 700 300 014", "Nangarhar"),
                ("Hina", "Ahmad", "hina.ahmad@demo.local", "+93 700 300 015", "Jalalabad"),
            ]
            customers = []
            for first_name, last_name, email, phone, city in customer_names:
                customer, _ = Customer.objects.get_or_create(
                    pharmacy=pharmacy,
                    email=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": phone,
                        "address": f"Demo street, {city}, Afghanistan",
                        "city": city,
                        "country": "AF",
                        "notes": "Synthetic demo customer record.",
                        "is_active": True,
                    },
                )
                if customer.first_name != first_name or customer.last_name != last_name:
                    customer.first_name = first_name
                    customer.last_name = last_name
                    customer.phone = phone
                    customer.city = city
                    customer.save(update_fields=["first_name", "last_name", "phone", "city"])
                customers.append(customer)

            accounts = {}
            account_specs = [
                ("1000", "Cash in Hand", "asset", 0, 1),
                ("1010", "Bank Account", "asset", 0, 2),
                ("1100", "Customer Receivables", "asset", 0, 3),
                ("1500", "Inventory Stock", "asset", 0, 4),
                ("2000", "Supplier Payables", "liability", 0, 5),
                ("3000", "Owner Equity", "equity", 0, 6),
                ("4000", "Sales Revenue", "revenue", 0, 7),
                ("5000", "Inventory Purchases", "expense", 0, 8),
                ("6000", "Operating Expense", "expense", 0, 9),
            ]
            for account_code, name, account_type, _, position_order in account_specs:
                account, _ = LedgerAccount.objects.get_or_create(
                    account_code=account_code,
                    defaults={
                        "name": name,
                        "account_type": account_type,
                        "currency": "AFN",
                        "pharmacy": pharmacy,
                        "position_order": position_order,
                        "is_active": True,
                    },
                )
                if account.name != name or account.account_type != account_type:
                    account.name = name
                    account.account_type = account_type
                    account.save(update_fields=["name", "account_type"])
                accounts[name] = account

            journal_code = "JE-INIT-001"
            initial_entry, created = JournalEntry.objects.get_or_create(
                journal_code=journal_code,
                defaults={
                    "entry_date": today,
                    "reference": "Initial demonstration inventory",
                    "description": "Seeded opening inventory balance for the demo pharmacy.",
                    "is_open": False,
                    "created_by": created_users["admin@pharmafin.local"],
                },
            )
            if not created:
                initial_entry.description = "Seeded opening inventory balance for the demo pharmacy."
                initial_entry.created_by = created_users["admin@pharmafin.local"]
                initial_entry.save(update_fields=["description", "created_by"])

            inventory_account = accounts["Inventory Stock"]
            cash_account = accounts["Cash in Hand"]
            JournalLine.objects.get_or_create(
                entry=initial_entry,
                account=inventory_account,
                defaults={"debit": Decimal("25000.00"), "credit": Decimal("0.00")},
            )
            JournalLine.objects.get_or_create(
                entry=initial_entry,
                account=cash_account,
                defaults={"debit": Decimal("0.00"), "credit": Decimal("25000.00")},
            )

        total_inventory = sum(batch.quantity for batch in MedicineBatch.objects.all())
        user_count = User.objects.count()
        pharmacy_count = Pharmacy.objects.count()
        branch_count = Branch.objects.count()
        warehouse_count = Warehouse.objects.count()
        category_count = MedicineCategory.objects.count()
        dosage_count = DosageForm.objects.count()
        manufacturer_count = Manufacturer.objects.count()
        medicine_count = Medicine.objects.count()
        batch_count = MedicineBatch.objects.count()
        supplier_count = Supplier.objects.count()
        customer_count = Customer.objects.count()
        ledger_account_count = LedgerAccount.objects.count()
        journal_entry_count = JournalEntry.objects.count()

        self.stdout.write("\n========================================")
        self.stdout.write("PharmaFin Demo Data Seeder")
        self.stdout.write("========================================")
        self.stdout.write(f"Users created: {user_count}")
        self.stdout.write(f"Pharmacies created: {pharmacy_count}")
        self.stdout.write(f"Branches created: {branch_count}")
        self.stdout.write(f"Warehouses created: {warehouse_count}")
        self.stdout.write(f"Categories created: {category_count}")
        self.stdout.write(f"Dosage forms created: {dosage_count}")
        self.stdout.write(f"Manufacturers created: {manufacturer_count}")
        self.stdout.write(f"Medicines created: {medicine_count}")
        self.stdout.write(f"Batches created: {batch_count}")
        self.stdout.write(f"Inventory units: {total_inventory}")
        self.stdout.write(f"Suppliers created: {supplier_count}")
        self.stdout.write(f"Customers created: {customer_count}")
        self.stdout.write(f"Ledger accounts created: {ledger_account_count}")
        self.stdout.write(f"Accounting journal entries: {journal_entry_count}")
        self.stdout.write("\nDemo data seeding completed successfully.")
        self.stdout.write("========================================")

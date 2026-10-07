from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.medicines.models import MedicineBatch
from .models import InventoryTransaction

_MOVEMENT_DIRECTIONS = {
    "purchase": "in",
    "receipt": "in",
    "sale_return": "in",
    "return": "in",
    "adjustment_in": "in",
    "transfer_in": "in",
    "sale": "out",
    "dispatch": "out",
    "purchase_return": "out",
    "adjustment_out": "out",
    "transfer_out": "out",
    "damage": "out",
    "expired": "out",
}
_MOVEMENT_DIRECTIONS["adjustment"] = None
_MOVEMENT_DIRECTIONS["transfer"] = None


def record_stock_movement(
    transaction_type: str,
    batch: MedicineBatch,
    branch,
    warehouse=None,
    quantity: int = 1,
    unit_price: Decimal = Decimal("0"),
    reference: str = "",
    created_by=None,
    direction: str | None = None,
    notes: str = "",
):
    """Atomically update one batch and append its stock-ledger movement."""
    qty = int(quantity)
    if qty <= 0:
        raise ValidationError("Quantity must be a positive integer.")
    if transaction_type not in _MOVEMENT_DIRECTIONS:
        raise ValidationError(f"Unsupported stock movement: {transaction_type}.")
    movement_direction = _MOVEMENT_DIRECTIONS[transaction_type] or direction
    if movement_direction not in {"in", "out"}:
        raise ValidationError("Direction must be 'in' or 'out'.")

    with transaction.atomic():
        locked_batch = (
            MedicineBatch.objects.select_for_update()
            .select_related("medicine")
            .get(pk=batch.pk)
        )
        if locked_batch.branch_id != branch.pk:
            raise ValidationError("Batch does not belong to the selected branch.")
        if warehouse and warehouse.branch_id != branch.pk:
            raise ValidationError("Warehouse does not belong to the selected branch.")
        if locked_batch.medicine.pharmacy_id not in (None, branch.pharmacy_id):
            raise ValidationError("Medicine does not belong to the selected pharmacy.")
        if movement_direction == "out":
            if transaction_type in {"sale", "dispatch"} and (
                locked_batch.status != "available"
                or locked_batch.expiry_date < date.today()
            ):
                raise ValidationError(
                    "Expired or unavailable batches cannot be dispatched."
                )
            if (
                transaction_type == "expired"
                and locked_batch.expiry_date >= date.today()
            ):
                raise ValidationError(
                    "Only expired batches can be recorded as expired stock."
                )
            if qty > locked_batch.quantity:
                raise ValidationError(
                    f"Insufficient stock for batch {locked_batch.batch_number}: "
                    f"available {locked_batch.quantity}, requested {qty}."
                )
            locked_batch.quantity -= qty
        else:
            locked_batch.quantity += qty

        if locked_batch.quantity == 0:
            locked_batch.status = "out_of_stock"
        elif locked_batch.expiry_date < date.today():
            locked_batch.status = "expired"
        elif locked_batch.status in {"out_of_stock", "expired"}:
            locked_batch.status = "available"
        locked_batch.save(update_fields=["quantity", "status", "updated_at"])

        movement = InventoryTransaction.objects.create(
            transaction_type=transaction_type,
            direction=movement_direction,
            batch=locked_batch,
            medicine=locked_batch.medicine,
            branch=branch,
            warehouse=warehouse,
            quantity=qty,
            unit_price=unit_price,
            reference=reference,
            notes=notes,
            created_by=created_by,
        )
    return movement


def fefo_batches(medicine, branch, quantity: int, status="available"):
    """Return exact stock allocations in earliest-expiry-first order."""
    requested = int(quantity)
    if requested <= 0:
        raise ValidationError("Quantity must be a positive integer.")
    if medicine.pharmacy_id not in (None, branch.pharmacy_id):
        raise ValidationError("Medicine does not belong to the selected pharmacy.")
    batches = (
        MedicineBatch.objects.filter(
            medicine=medicine,
            branch=branch,
            status=status,
            expiry_date__gte=date.today(),
            quantity__gt=0,
        )
        .order_by("expiry_date", "id")
        .select_related("branch", "warehouse", "medicine")
    )
    allocations = []
    remaining = requested
    total_available = 0
    for batch in batches:
        total_available += batch.quantity
        if remaining == 0:
            continue
        allocated = min(batch.quantity, remaining)
        allocations.append({"batch": batch, "quantity": allocated})
        remaining -= allocated
    if remaining:
        raise ValidationError(
            f"Not enough available stock for {medicine} at {branch}: "
            f"available {total_available}, requested {requested}."
        )
    return allocations, remaining


class FEFOAllocationService:
    """Small injectable facade for FEFO stock planning."""

    @staticmethod
    def allocate(medicine, branch, quantity: int):
        return fefo_batches(medicine, branch, quantity)


@transaction.atomic
def transfer_stock(
    source: MedicineBatch,
    destination: MedicineBatch,
    quantity: int,
    created_by=None,
    reference: str = "",
    notes: str = "",
):
    """Move stock between existing batches with paired ledger entries."""
    if source.pk == destination.pk:
        raise ValidationError("Source and destination batches must be different.")
    locks = list(
        MedicineBatch.objects.select_for_update()
        .filter(pk__in=sorted((source.pk, destination.pk)))
        .order_by("pk")
    )
    if len(locks) != 2:
        raise ValidationError("Source or destination batch no longer exists.")
    source_locked, destination_locked = (
        (locks[0], locks[1])
        if locks[0].pk == source.pk
        else (locks[1], locks[0])
    )
    if source_locked.medicine_id != destination_locked.medicine_id:
        raise ValidationError(
            "Stock can only transfer between batches of one medicine."
        )
    if (
        source_locked.branch.pharmacy_id != destination_locked.branch.pharmacy_id
        or source_locked.medicine.pharmacy_id
        not in (None, source_locked.branch.pharmacy_id)
    ):
        raise ValidationError("Transfers cannot cross pharmacy tenants.")
    if (
        source_locked.expiry_date < date.today()
        or source_locked.status != "available"
    ):
        raise ValidationError("Unavailable batches cannot be transferred from.")
    if (
        destination_locked.expiry_date < date.today()
        or destination_locked.status in {"recalled", "damaged"}
    ):
        raise ValidationError(
            "Stock cannot be transferred into an unavailable batch."
        )
    transfer_reference = reference or f"TRANSFER-{source.pk}-{destination.pk}"
    outbound = record_stock_movement(
        "transfer_out",
        source_locked,
        source_locked.branch,
        source_locked.warehouse,
        quantity,
        source_locked.purchase_price,
        f"{transfer_reference}-OUT",
        created_by,
        notes=notes,
    )
    inbound = record_stock_movement(
        "transfer_in",
        destination_locked,
        destination_locked.branch,
        destination_locked.warehouse,
        quantity,
        destination_locked.purchase_price,
        f"{transfer_reference}-IN",
        created_by,
        notes=notes,
    )
    return outbound, inbound


# Compatibility for existing callers; the implementation is FEFO ordered.
fifo_batches = fefo_batches

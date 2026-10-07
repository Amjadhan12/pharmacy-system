from decimal import Decimal
from datetime import date

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.medicines.models import MedicineBatch
from .models import InventoryTransaction


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
):
    """Append a stock movement and update its batch under a row lock.

    Raises ``ValidationError`` when a dispatch would drive the batch quantity
    negative (negative-stock protection).
    """
    qty = int(quantity)
    if qty <= 0:
        raise ValidationError("Quantity must be a positive integer.")
    if transaction_type not in {"receipt", "dispatch", "adjustment", "return"}:
        raise ValidationError(f"Unsupported stock movement: {transaction_type}.")
    movement_direction = direction or (
        "out" if transaction_type == "dispatch" else "in"
    )
    if movement_direction not in {"in", "out"}:
        raise ValidationError("Direction must be 'in' or 'out'.")
    if transaction_type == "dispatch":
        movement_direction = "out"
    if transaction_type == "receipt" or transaction_type == "return":
        movement_direction = "in"

    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().select_related(
            "medicine"
        ).get(pk=batch.pk)
        if locked_batch.branch_id != branch.pk:
            raise ValidationError("Batch does not belong to the selected branch.")
        if warehouse and warehouse.branch_id != branch.pk:
            raise ValidationError("Warehouse does not belong to the selected branch.")
        if movement_direction == "out":
            if (
                transaction_type == "dispatch"
                and (
                    locked_batch.status != "available"
                    or locked_batch.expiry_date < date.today()
                )
            ):
                raise ValidationError("Expired or unavailable batches cannot be dispatched.")
            available = locked_batch.quantity
            if qty > available:
                raise ValidationError(
                    f"Insufficient stock for batch {locked_batch.batch_number}: "
                    f"available {available}, requested {qty}."
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
        locked_batch.save(update_fields=["quantity", "status"])

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
            created_by=created_by,
        )

    return movement


def fifo_batches(medicine, branch, qty, status="available"):
    """Return (allocation list, remaining) ordered by earliest expiry (FEFO)."""
    if int(qty) <= 0:
        raise ValidationError("Quantity must be a positive integer.")
    allocation = []
    remaining = int(qty)
    batches = (
        MedicineBatch.objects.filter(
            medicine=medicine,
            branch=branch,
            status=status,
            expiry_date__gte=date.today(),
            quantity__gt=0,
        )
        .order_by("expiry_date", "id")
        .select_related("branch", "warehouse")
    )
    for b in batches:
        if remaining <= 0:
            break
        take = min(b.quantity, remaining)
        allocation.append({"batch": b, "quantity": take})
        remaining -= take

    if remaining > 0:
        raise ValidationError(
            f"Not enough available stock for {medicine} at {branch}: "
            f"available {sum(b['batch'].quantity for b in allocation)}, "
            f"requested {qty}."
        )
    return allocation, remaining

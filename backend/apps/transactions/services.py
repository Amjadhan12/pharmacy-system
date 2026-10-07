from decimal import Decimal

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
):
    """Atomically append an inventory movement and update the batch quantity.

    Raises ``ValidationError`` when a dispatch would drive the batch quantity
    negative (negative-stock protection).
    """
    qty = int(quantity)
    if qty <= 0:
        raise ValidationError("Quantity must be a positive integer.")

    with transaction.atomic():
        if transaction_type == "dispatch":
            available = batch.quantity
            if qty > available:
                raise ValidationError(
                    f"Insufficient stock for batch {batch.batch_number}: "
                    f"available {available}, requested {qty}."
                )
            batch.quantity -= qty
            batch.save(update_fields=["quantity"])
        elif transaction_type == "receipt":
            batch.quantity += qty
            batch.save(update_fields=["quantity"])
        elif transaction_type == "return":
            # A return restores stock to the batch.
            batch.quantity += qty
            batch.save(update_fields=["quantity"])
        elif transaction_type == "adjustment":
            # Caller is expected to pass the signed magnitude; this moves by
            # ``qty`` regardless of direction.
            new_qty = batch.quantity + qty
            if new_qty < 0:
                raise ValidationError("Adjustment would drive the batch quantity negative.")
            batch.quantity = new_qty
            batch.save(update_fields=["quantity"])
        else:
            raise ValidationError(f"Unknown transaction type: {transaction_type}")

        transaction = InventoryTransaction.objects.create(
            transaction_type=transaction_type,
            batch=batch,
            medicine=batch.medicine,
            branch=branch,
            warehouse=warehouse,
            quantity=qty,
            unit_price=unit_price,
            reference=reference,
            created_by=created_by,
        )

    return transaction


def fifo_batches(medicine, branch, qty, status="available"):
    """Return (allocation list, remaining) ordered by earliest expiry (FEFO)."""
    allocation = []
    remaining = int(qty)
    batches = (
        MedicineBatch.objects.filter(
            medicine=medicine, branch=branch, status=status
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


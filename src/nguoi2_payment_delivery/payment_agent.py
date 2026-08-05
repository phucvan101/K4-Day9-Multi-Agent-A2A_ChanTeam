"""Payment Agent — sở hữu: Người 2.

Input: claimed_order_id
Output: PaymentReconciliation (expected_total_brl, payment_total_brl,
        difference_brl, reconciled), kèm payment_ids để Coordinator
        ghép vào affected_entities.payment_ids
Đọc: order_payments.csv, order_items.csv
Công thức: README mục 4 (expected_total_brl, difference_brl, reconciled)
"""

from src.common.data_loader import load_items, load_payments
from src.common.schema import PaymentReconciliation


def _round_brl(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def run(claimed_order_id: str) -> tuple[PaymentReconciliation, list[str]]:
    items = load_items(claimed_order_id)
    payments = load_payments(claimed_order_id)

    payment_ids = [
        f"{claimed_order_id}:{int(payment['payment_sequential'])}" for payment in payments
    ][:5]
    payment_total_brl = _round_brl(sum(float(payment["payment_value"]) for payment in payments))
    payment_types = list(dict.fromkeys(payment["payment_type"] for payment in payments))

    if not items:
        reconciliation = PaymentReconciliation(
            payment_total_brl=payment_total_brl,
            payment_types=payment_types,
        )
        return reconciliation, payment_ids

    item_total_brl = _round_brl(sum(float(item["price"]) for item in items))
    freight_total_brl = _round_brl(sum(float(item["freight_value"]) for item in items))
    expected_total_brl = _round_brl((item_total_brl or 0.0) + (freight_total_brl or 0.0))
    difference_brl = _round_brl((payment_total_brl or 0.0) - (expected_total_brl or 0.0))

    reconciliation = PaymentReconciliation(
        item_total_brl=item_total_brl,
        freight_total_brl=freight_total_brl,
        expected_total_brl=expected_total_brl,
        payment_total_brl=payment_total_brl,
        difference_brl=difference_brl,
        reconciled=abs(difference_brl or 0.0) <= 0.10,
        payment_types=payment_types,
    )
    return reconciliation, payment_ids

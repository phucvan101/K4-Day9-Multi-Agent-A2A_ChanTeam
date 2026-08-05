"""Payment Agent — sở hữu: Người 2.

Input: claimed_order_id
Output: PaymentReconciliation (expected_total_brl, payment_total_brl,
        difference_brl, reconciled), cờ split_payment
Đọc: order_payments.csv, order_items.csv
Công thức: README mục 4 (expected_total_brl, difference_brl, reconciled)
"""

from src.common.schema import PaymentReconciliation


def run(claimed_order_id: str) -> PaymentReconciliation:
    raise NotImplementedError

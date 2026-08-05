"""Customer Agent — sở hữu: Người 1.

Input: claimed_order_id
Output: CustomerContext (customer_unique_id, related_order_ids, cờ repeat_customer)
Đọc: customers.csv, orders.csv
"""

from src.common.data_loader import load_customer_history, load_order
from src.common.schema import CustomerContext


def run(claimed_order_id: str) -> CustomerContext:
    order = load_order(claimed_order_id)
    if order is None:
        return CustomerContext()

    related_order_ids = load_customer_history(
        order["customer_unique_id"], exclude_order_id=claimed_order_id
    )
    return CustomerContext(
        customer_unique_id=order["customer_unique_id"],
        related_order_ids=related_order_ids[:5],
    )

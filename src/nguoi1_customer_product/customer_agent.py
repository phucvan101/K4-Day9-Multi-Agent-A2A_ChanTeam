"""Customer Agent — sở hữu: Người 1.

Input: claimed_order_id
Output: CustomerContext (customer_unique_id, related_order_ids, cờ repeat_customer)
Đọc: customers.csv, orders.csv
"""

from src.common.schema import CustomerContext


def run(claimed_order_id: str) -> CustomerContext:
    raise NotImplementedError

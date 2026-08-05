"""Delivery Agent — sở hữu: Người 2.

Input: claimed_order_id
Output: DeliveryAnalysis (delivery_variance_hours, seller_handoff_analysis,
        late_handoff_seller_ids)
Đọc: orders.csv, order_items.csv (shipping_limit_date theo seller)
Công thức: README mục 4 (delivery_variance_hours, handoff_variance_hours)
"""

from src.common.schema import DeliveryAnalysis


def run(claimed_order_id: str) -> DeliveryAnalysis:
    raise NotImplementedError

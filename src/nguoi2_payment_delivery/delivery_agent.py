"""Delivery Agent — sở hữu: Người 2.

Input: claimed_order_id
Output: DeliveryAnalysis (delivery_variance_hours, seller_handoff_analysis,
        late_handoff_seller_ids)
Đọc: orders.csv, order_items.csv (shipping_limit_date theo seller)
Công thức: README mục 4 (delivery_variance_hours, handoff_variance_hours)
"""

from datetime import datetime

from src.common.data_loader import load_items, load_order
from src.common.schema import DeliveryAnalysis, SellerHandoff


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None or value != value:
        return None
    return datetime.strptime(value, DATETIME_FORMAT)


def _round_hours(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def _variance_hours(later_at: str | None, earlier_at: str | None) -> float | None:
    later_dt = _parse_timestamp(later_at)
    earlier_dt = _parse_timestamp(earlier_at)
    if later_dt is None or earlier_dt is None:
        return None
    delta = later_dt - earlier_dt
    return _round_hours(delta.total_seconds() / 3600)


def run(claimed_order_id: str) -> DeliveryAnalysis:
    order = load_order(claimed_order_id)
    if order is None:
        return DeliveryAnalysis()

    items = load_items(claimed_order_id)
    delivered_at = order.get("order_delivered_customer_date")
    estimated_delivery_at = order.get("order_estimated_delivery_date")
    carrier_handoff_at = order.get("order_delivered_carrier_date")
    delivery_variance_hours = _variance_hours(delivered_at, estimated_delivery_at)

    seller_handoff_analysis: list[SellerHandoff] = []
    late_handoff_seller_ids: list[str] = []

    earliest_shipping_limit_by_seller: dict[str, str] = {}
    for item in items:
        seller_id = item["seller_id"]
        shipping_limit_at = item.get("shipping_limit_date")
        if seller_id not in earliest_shipping_limit_by_seller:
            earliest_shipping_limit_by_seller[seller_id] = shipping_limit_at
        elif shipping_limit_at < earliest_shipping_limit_by_seller[seller_id]:
            earliest_shipping_limit_by_seller[seller_id] = shipping_limit_at

    for seller_id, shipping_limit_at in earliest_shipping_limit_by_seller.items():
        handoff_variance_hours = _variance_hours(carrier_handoff_at, shipping_limit_at)
        late_handoff = handoff_variance_hours is not None and handoff_variance_hours > 0
        if late_handoff:
            late_handoff_seller_ids.append(seller_id)
        seller_handoff_analysis.append(
            SellerHandoff(
                seller_id=seller_id,
                shipping_limit_at=shipping_limit_at,
                handoff_variance_hours=handoff_variance_hours,
                late_handoff=late_handoff,
            )
        )

    return DeliveryAnalysis(
        delivered_at=delivered_at,
        estimated_delivery_at=estimated_delivery_at,
        carrier_handoff_at=carrier_handoff_at,
        delivery_variance_hours=delivery_variance_hours,
        seller_handoff_analysis=seller_handoff_analysis,
        late_handoff_seller_ids=late_handoff_seller_ids[:3],
    )

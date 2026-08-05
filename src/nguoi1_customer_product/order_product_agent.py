"""Order & Product Agent — sở hữu: Người 1.

Input: claimed_order_id
Output: AffectedEntities (order/item/seller ids), ProductContext,
        cờ multi_item_order / multi_seller_order / multiple_categories
Đọc: orders.csv, order_items.csv, products.csv, sellers.csv
"""

from src.common.schema import AffectedEntities, ProductContext


def run(claimed_order_id: str) -> tuple[AffectedEntities, ProductContext]:
    raise NotImplementedError

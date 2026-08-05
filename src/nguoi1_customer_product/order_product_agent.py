"""Order & Product Agent — sở hữu: Người 1.

Input: claimed_order_id
Output: AffectedEntities (order/item/seller ids), ProductContext,
        cờ multi_item_order / multi_seller_order / multiple_categories
Đọc: orders.csv, order_items.csv, products.csv, sellers.csv
"""

from src.common.data_loader import load_items, load_products
from src.common.schema import AffectedEntities, ProductContext


def run(claimed_order_id: str) -> tuple[AffectedEntities, ProductContext]:
    items = load_items(claimed_order_id)

    item_ids = [f"{claimed_order_id}:{i['order_item_id']}" for i in items]
    seller_ids = list(dict.fromkeys(i["seller_id"] for i in items))
    product_ids = list(dict.fromkeys(i["product_id"] for i in items))

    affected = AffectedEntities(
        order_ids=[claimed_order_id],
        item_ids=item_ids[:5],
        seller_ids=seller_ids[:3],
    )

    products = load_products(product_ids)
    category_names = list(dict.fromkeys(p["product_category_name"] for p in products))
    product_context = ProductContext(
        product_ids=product_ids[:5],
        category_names=category_names[:5],
    )
    return affected, product_context

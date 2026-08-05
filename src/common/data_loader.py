"""Load và join các CSV trong data/ theo khóa join ở README mục 2.

Dùng chung cho toàn bộ agent — không lặp lại logic đọc CSV ở từng module.
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_order(order_id: str) -> dict:
    """Trả về row orders.csv khớp order_id, kèm các bảng liên quan đã join."""
    raise NotImplementedError


def load_customer_history(customer_unique_id: str) -> list[str]:
    """Trả về related_order_ids của cùng customer_unique_id (loại trừ order hiện tại)."""
    raise NotImplementedError


def load_items(order_id: str) -> list[dict]:
    raise NotImplementedError


def load_payments(order_id: str) -> list[dict]:
    raise NotImplementedError


def load_sellers(seller_ids: list[str]) -> list[dict]:
    raise NotImplementedError


def load_products(product_ids: list[str]) -> list[dict]:
    raise NotImplementedError

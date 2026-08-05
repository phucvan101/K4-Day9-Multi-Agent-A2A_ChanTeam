"""Load và join các CSV trong data/ theo khóa join ở README mục 2.

Dùng chung cho toàn bộ agent — không lặp lại logic đọc CSV ở từng module.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=1)
def _orders_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")


@lru_cache(maxsize=1)
def _customers_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")


def load_order(order_id: str) -> dict | None:
    """Trả về row orders.csv khớp order_id, kèm customer_unique_id đã join."""
    row = _orders_df().loc[_orders_df()["order_id"] == order_id]
    if row.empty:
        return None
    order = row.iloc[0].to_dict()

    customer_row = _customers_df().loc[
        _customers_df()["customer_id"] == order["customer_id"]
    ]
    order["customer_unique_id"] = (
        customer_row.iloc[0]["customer_unique_id"] if not customer_row.empty else None
    )
    return order


def load_customer_history(customer_unique_id: str, exclude_order_id: str) -> list[str]:
    """Trả về related_order_ids của cùng customer_unique_id (loại trừ order hiện tại)."""
    same_customer = _customers_df().loc[
        _customers_df()["customer_unique_id"] == customer_unique_id
    ]
    orders = _orders_df().loc[
        _orders_df()["customer_id"].isin(same_customer["customer_id"])
    ]
    order_ids = orders["order_id"].tolist()
    return [oid for oid in order_ids if oid != exclude_order_id]


@lru_cache(maxsize=1)
def _items_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")


def load_items(order_id: str) -> list[dict]:
    """Với order không có item row nào, trả về [] (README mục 4)."""
    rows = _items_df().loc[_items_df()["order_id"] == order_id]
    return rows.to_dict("records")


@lru_cache(maxsize=1)
def _payments_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")


def load_payments(order_id: str) -> list[dict]:
    rows = _payments_df().loc[_payments_df()["order_id"] == order_id]
    return rows.to_dict("records")


@lru_cache(maxsize=1)
def _sellers_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")


def load_sellers(seller_ids: list[str]) -> list[dict]:
    rows = _sellers_df().loc[_sellers_df()["seller_id"].isin(seller_ids)]
    return rows.to_dict("records")


@lru_cache(maxsize=1)
def _products_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "olist_products_dataset.csv")


def load_products(product_ids: list[str]) -> list[dict]:
    rows = _products_df().loc[_products_df()["product_id"].isin(product_ids)]
    return rows.to_dict("records")

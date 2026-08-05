"""Contract dùng chung giữa các agent — khớp README mục 6 (Output schema).

Mọi agent handoff dữ liệu qua các dataclass ở đây thay vì dict tự do,
để Verifier Agent (nguoi4) kiểm tra được field/limit một cách nhất quán.
"""

from dataclasses import dataclass, field


@dataclass
class CustomerContext:
    customer_unique_id: str | None = None
    related_order_ids: list[str] = field(default_factory=list)


@dataclass
class ProductContext:
    product_ids: list[str] = field(default_factory=list)
    category_names: list[str] = field(default_factory=list)


@dataclass
class AffectedEntities:
    order_ids: list[str] = field(default_factory=list)
    item_ids: list[str] = field(default_factory=list)
    seller_ids: list[str] = field(default_factory=list)
    payment_ids: list[str] = field(default_factory=list)


@dataclass
class PaymentReconciliation:
    currency: str = "BRL"
    item_total_brl: float | None = None
    freight_total_brl: float | None = None
    expected_total_brl: float | None = None
    payment_total_brl: float | None = None
    difference_brl: float | None = None
    reconciled: bool | None = None
    payment_types: list[str] = field(default_factory=list)


@dataclass
class SellerHandoff:
    seller_id: str
    shipping_limit_at: str | None
    handoff_variance_hours: float | None
    late_handoff: bool


@dataclass
class DeliveryAnalysis:
    delivered_at: str | None = None
    estimated_delivery_at: str | None = None
    carrier_handoff_at: str | None = None
    delivery_variance_hours: float | None = None
    seller_handoff_analysis: list[SellerHandoff] = field(default_factory=list)
    late_handoff_seller_ids: list[str] = field(default_factory=list)


@dataclass
class CaseContext:
    """Case context dùng chung, Coordinator (nguoi4) khởi tạo và truyền qua từng agent."""

    case_id: str
    claimed_order_id: str
    customer_context: CustomerContext = field(default_factory=CustomerContext)
    product_context: ProductContext = field(default_factory=ProductContext)
    affected_entities: AffectedEntities = field(default_factory=AffectedEntities)
    payment_reconciliation: PaymentReconciliation = field(default_factory=PaymentReconciliation)
    delivery_analysis: DeliveryAnalysis = field(default_factory=DeliveryAnalysis)

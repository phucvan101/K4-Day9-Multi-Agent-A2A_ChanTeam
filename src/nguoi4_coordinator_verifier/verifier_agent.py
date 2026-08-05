"""Verifier Agent — sở hữu: Người 4.

Kiểm schema, evidence ID có tồn tại thật trong CSV, array limit (README mục 6),
null handling trước khi Coordinator ghi output/EC_xxx.json.

Trả về (True, None) nếu hợp lệ, (False, lý do) nếu reject để Coordinator
re-dispatch lại agent liên quan.
"""


def verify(case_output: dict) -> tuple[bool, str | None]:
    raise NotImplementedError


def verify_evidence_ids_exist(evidence_ids: list[str]) -> bool:
    raise NotImplementedError


def verify_array_limits(case_output: dict) -> bool:
    """order_ids<=5, item_ids<=5, seller_ids<=3, payment_ids<=5, related_order_ids<=5,
    product_ids<=5, category<=5, root causes<=3, responsible parties<=3,
    evidence<=20, actions<=5 (README mục 6)."""
    raise NotImplementedError

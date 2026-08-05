"""Verifier Agent — sở hữu: Người 4.

Kiểm schema, evidence ID có tồn tại thật trong CSV, array limit (README mục 6),
null handling trước khi Coordinator ghi output/EC_xxx.json.

Trả về (True, None) nếu hợp lệ, (False, lý do) nếu reject để Coordinator
re-dispatch lại agent liên quan.
"""

from src.common.data_loader import load_items, load_order, load_payments, load_sellers

VALID_PRIMARY_ISSUES = {
    "canceled_order_paid",
    "unavailable_order_paid",
    "late_delivery_seller",
    "late_delivery_logistics",
    "valid_split_payment",
    "unsupported_late_claim",
}

VALID_SECONDARY_ISSUES = {
    "multi_item_order",
    "multi_seller_order",
    "split_payment",
    "repeat_customer",
    "multiple_categories",
}

VALID_CASE_STATUSES = {"action_required", "no_action"}
VALID_ROOT_CAUSES = {
    "SELLER_HANDOFF_AFTER_LIMIT",
    "CARRIER_DELIVERED_AFTER_ESTIMATE",
    "ORDER_CANCELED_AFTER_PAYMENT",
    "ORDER_UNAVAILABLE_AFTER_PAYMENT",
    "MULTIPLE_PAYMENTS_RECONCILED",
    "DELIVERY_WITHIN_ESTIMATE",
}

REQUIRED_TOP_LEVEL_KEYS = {
    "case_id",
    "case_assessment",
    "affected_entities",
    "customer_context",
    "product_context",
    "delivery_analysis",
    "payment_reconciliation",
    "root_cause_analysis",
    "evidence_ids",
    "financial_resolution",
    "resolution_actions",
}

ARRAY_LIMITS = {
    ("affected_entities", "order_ids"): 5,
    ("affected_entities", "item_ids"): 5,
    ("affected_entities", "seller_ids"): 3,
    ("affected_entities", "payment_ids"): 5,
    ("customer_context", "related_order_ids"): 5,
    ("product_context", "product_ids"): 5,
    ("product_context", "category_names"): 5,
    ("root_cause_analysis", "ranked_causes"): 3,
    ("root_cause_analysis", "responsible_parties"): 3,
    ("case_assessment", "secondary_issues"): 5,
    ("evidence_ids",): 20,
    ("resolution_actions",): 5,
}


def _get_nested(case_output: dict, path: tuple[str, ...]):
    current = case_output
    for key in path:
        current = current[key]
    return current


def verify(case_output: dict) -> tuple[bool, str | None]:
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - case_output.keys()
    if missing_keys:
        return False, f"missing_top_level_keys:{sorted(missing_keys)}"

    assessment = case_output["case_assessment"]
    if assessment["primary_issue"] not in VALID_PRIMARY_ISSUES:
        return False, "invalid_primary_issue"
    if any(issue not in VALID_SECONDARY_ISSUES for issue in assessment["secondary_issues"]):
        return False, "invalid_secondary_issue"
    if assessment["case_status"] not in VALID_CASE_STATUSES:
        return False, "invalid_case_status"

    confidence = assessment["confidence"]
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return False, "invalid_confidence"

    ranked_causes = case_output["root_cause_analysis"]["ranked_causes"]
    if not ranked_causes:
        return False, "missing_ranked_causes"
    if any(cause["cause_code"] not in VALID_ROOT_CAUSES for cause in ranked_causes):
        return False, "invalid_root_cause"

    if not verify_array_limits(case_output):
        return False, "array_limit_exceeded"

    if not verify_evidence_ids_exist(case_output["evidence_ids"]):
        return False, "invalid_evidence_ids"

    recommended_refund = case_output["financial_resolution"]["recommended_refund_brl"]
    if recommended_refund is None or recommended_refund < 0:
        return False, "invalid_financial_resolution"

    if not isinstance(case_output["resolution_actions"], list):
        return False, "invalid_resolution_actions"

    return True, None


def verify_evidence_ids_exist(evidence_ids: list[str]) -> bool:
    for evidence_id in evidence_ids:
        try:
            evidence_type, payload = evidence_id.split(":", 1)
        except ValueError:
            return False

        if evidence_type == "order":
            if load_order(payload) is None:
                return False
        elif evidence_type == "item":
            order_id, item_id_raw = payload.rsplit(":", 1)
            items = load_items(order_id)
            if not any(str(int(item["order_item_id"])) == item_id_raw for item in items):
                return False
        elif evidence_type == "payment":
            order_id, payment_seq_raw = payload.rsplit(":", 1)
            payments = load_payments(order_id)
            if not any(
                str(int(payment["payment_sequential"])) == payment_seq_raw
                for payment in payments
            ):
                return False
        elif evidence_type == "seller":
            if not load_sellers([payload]):
                return False
        elif evidence_type == "policy":
            if payload not in VALID_ROOT_CAUSES:
                return False
        else:
            return False
    return True


def verify_array_limits(case_output: dict) -> bool:
    """order_ids<=5, item_ids<=5, seller_ids<=3, payment_ids<=5, related_order_ids<=5,
    product_ids<=5, category<=5, root causes<=3, responsible parties<=3,
    evidence<=20, actions<=5 (README mục 6)."""
    for path, limit in ARRAY_LIMITS.items():
        value = _get_nested(case_output, path)
        if not isinstance(value, list) or len(value) > limit:
            return False
    return True

"""Policy Agent — sở hữu: Người 3.

Không đọc CSV trực tiếp; chỉ nhận case context đã tổng hợp từ
Customer/Order&Product/Payment/Delivery Agent.

Input: CaseContext (customer_context, product_context, affected_entities,
       payment_reconciliation, delivery_analysis)
Output: case_assessment, root_cause_analysis, financial_resolution,
        resolution_actions, evidence_ids
Áp dụng: EC_POLICY_V2 theo đúng thứ tự ưu tiên ở README mục 4.
"""

from src.common.schema import CaseContext

ISSUE_TO_ROOT_CAUSE = {
    "canceled_order_paid": "ORDER_CANCELED_AFTER_PAYMENT",
    "unavailable_order_paid": "ORDER_UNAVAILABLE_AFTER_PAYMENT",
    "late_delivery_seller": "SELLER_HANDOFF_AFTER_LIMIT",
    "late_delivery_logistics": "CARRIER_DELIVERED_AFTER_ESTIMATE",
    "valid_split_payment": "MULTIPLE_PAYMENTS_RECONCILED",
    "unsupported_late_claim": "DELIVERY_WITHIN_ESTIMATE",
}

ISSUE_TO_CONFIDENCE = {
    "canceled_order_paid": 0.98,
    "unavailable_order_paid": 0.98,
    "late_delivery_seller": 0.94,
    "late_delivery_logistics": 0.93,
    "valid_split_payment": 0.97,
    "unsupported_late_claim": 0.96,
}


def _round_money(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def _payment_count(case: CaseContext) -> int:
    return len(case.affected_entities.payment_ids)


def _has_late_delivery(case: CaseContext) -> bool:
    variance = case.delivery_analysis.delivery_variance_hours
    return variance is not None and variance > 0


def _is_reconciled(case: CaseContext) -> bool:
    return case.payment_reconciliation.reconciled is True


def _has_payment(case: CaseContext) -> bool:
    total = case.payment_reconciliation.payment_total_brl
    return total is not None and total > 0


def determine_primary_issue(case: CaseContext) -> str:
    if case.order_status == "canceled" and _has_payment(case):
        return "canceled_order_paid"
    if case.order_status == "unavailable" and _has_payment(case):
        return "unavailable_order_paid"
    if _has_late_delivery(case) and case.delivery_analysis.late_handoff_seller_ids:
        return "late_delivery_seller"
    if _has_late_delivery(case) and not case.delivery_analysis.late_handoff_seller_ids:
        return "late_delivery_logistics"
    if _payment_count(case) >= 2 and _is_reconciled(case):
        return "valid_split_payment"
    return "unsupported_late_claim"


def determine_secondary_issues(case: CaseContext) -> list[str]:
    secondary_issues: list[str] = []

    if len(case.affected_entities.item_ids) >= 2:
        secondary_issues.append("multi_item_order")
    if len(case.affected_entities.seller_ids) >= 2:
        secondary_issues.append("multi_seller_order")
    if _payment_count(case) >= 2:
        secondary_issues.append("split_payment")
    if case.customer_context.related_order_ids:
        secondary_issues.append("repeat_customer")
    if len(case.product_context.category_names) >= 2:
        secondary_issues.append("multiple_categories")

    return secondary_issues


def build_evidence_ids(case: CaseContext, root_cause_code: str) -> list[str]:
    """Chỉ sinh evidence ID theo định dạng README mục 5, dựng được từ dữ liệu thật."""
    evidence_ids: list[str] = []

    evidence_ids.append(f"order:{case.claimed_order_id}")
    evidence_ids.extend(f"item:{item_id}" for item_id in case.affected_entities.item_ids)
    evidence_ids.extend(
        f"payment:{payment_id}" for payment_id in case.affected_entities.payment_ids
    )
    evidence_ids.extend(
        f"seller:{seller_id}" for seller_id in case.affected_entities.seller_ids
    )
    evidence_ids.append(f"policy:{root_cause_code}")

    return evidence_ids[:20]


def _build_root_cause_analysis(case: CaseContext, primary_issue: str) -> dict:
    root_cause_code = ISSUE_TO_ROOT_CAUSE[primary_issue]
    responsible_parties: list[dict] = []

    if primary_issue in {"canceled_order_paid", "unavailable_order_paid"}:
        responsible_parties.append(
            {"party_type": "platform", "party_id": "OLIST_PLATFORM"}
        )
    elif primary_issue == "late_delivery_seller":
        for seller_id in case.delivery_analysis.late_handoff_seller_ids[:3]:
            responsible_parties.append({"party_type": "seller", "party_id": seller_id})
    elif primary_issue == "late_delivery_logistics":
        responsible_parties.append(
            {"party_type": "logistics_provider", "party_id": "LOGISTICS_PROVIDER"}
        )

    return {
        "ranked_causes": [{"cause_code": root_cause_code, "rank": 1}],
        "responsible_parties": responsible_parties[:3],
    }


def _build_financial_resolution(case: CaseContext, primary_issue: str) -> dict:
    if primary_issue in {"canceled_order_paid", "unavailable_order_paid"}:
        refund = _round_money(case.payment_reconciliation.payment_total_brl)
    elif primary_issue in {"late_delivery_seller", "late_delivery_logistics"}:
        refund = _round_money(case.payment_reconciliation.freight_total_brl)
    else:
        refund = 0.0

    return {"currency": "BRL", "recommended_refund_brl": refund}


def _build_actions(case: CaseContext, primary_issue: str) -> list[str]:
    actions: list[str] = []

    if primary_issue in {"canceled_order_paid", "unavailable_order_paid"}:
        actions.append("issue_full_refund")
    elif primary_issue in {"late_delivery_seller", "late_delivery_logistics"}:
        actions.append("refund_freight")
    elif primary_issue == "valid_split_payment":
        actions.append("explain_valid_split_payment")
    else:
        actions.append("reject_late_refund")

    if primary_issue == "late_delivery_seller":
        actions.append("review_seller_handoff")
    elif primary_issue == "late_delivery_logistics":
        actions.append("review_carrier_delay")

    if primary_issue in {
        "canceled_order_paid",
        "unavailable_order_paid",
        "late_delivery_seller",
        "late_delivery_logistics",
    }:
        actions.append("verify_refund_completion")

    if len(case.affected_entities.seller_ids) >= 2:
        actions.append("coordinate_multi_seller_case")

    if _payment_count(case) >= 2 and primary_issue != "valid_split_payment":
        actions.append("verify_payment_allocation")

    return actions[:5]


def run(case: CaseContext) -> dict:
    primary_issue = determine_primary_issue(case)
    secondary_issues = determine_secondary_issues(case)
    root_cause_code = ISSUE_TO_ROOT_CAUSE[primary_issue]

    case_assessment = {
        "primary_issue": primary_issue,
        "secondary_issues": secondary_issues,
        "case_status": (
            "action_required"
            if primary_issue
            in {
                "canceled_order_paid",
                "unavailable_order_paid",
                "late_delivery_seller",
                "late_delivery_logistics",
            }
            else "no_action"
        ),
        "confidence": ISSUE_TO_CONFIDENCE[primary_issue],
    }

    root_cause_analysis = _build_root_cause_analysis(case, primary_issue)
    evidence_ids = build_evidence_ids(case, root_cause_code)
    financial_resolution = _build_financial_resolution(case, primary_issue)
    resolution_actions = _build_actions(case, primary_issue)

    return {
        "case_assessment": case_assessment,
        "root_cause_analysis": root_cause_analysis,
        "evidence_ids": evidence_ids,
        "financial_resolution": financial_resolution,
        "resolution_actions": resolution_actions,
    }

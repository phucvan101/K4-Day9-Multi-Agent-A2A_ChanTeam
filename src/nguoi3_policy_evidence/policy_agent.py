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


def determine_primary_issue(case: CaseContext) -> str:
    raise NotImplementedError


def determine_secondary_issues(case: CaseContext) -> list[str]:
    raise NotImplementedError


def build_evidence_ids(case: CaseContext, root_cause_code: str) -> list[str]:
    """Chỉ sinh evidence ID theo định dạng README mục 5, dựng được từ dữ liệu thật."""
    raise NotImplementedError


def run(case: CaseContext) -> dict:
    raise NotImplementedError

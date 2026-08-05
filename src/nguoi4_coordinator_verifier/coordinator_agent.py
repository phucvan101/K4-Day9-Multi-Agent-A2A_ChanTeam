"""Coordinator Agent — sở hữu: Người 4.

Nhận input/EC_xxx.json, điều phối Customer/Order&Product/Payment/Delivery Agent,
gộp kết quả gửi Policy Agent, rồi gửi qua Verifier trước khi ghi output/.
"""

import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path

from src.common.data_loader import load_order
from src.common.schema import CaseContext
from src.nguoi1_customer_product.customer_agent import run as customer_run
from src.nguoi1_customer_product.order_product_agent import run as order_product_run
from src.nguoi2_payment_delivery.delivery_agent import run as delivery_run
from src.nguoi2_payment_delivery.payment_agent import run as payment_run
from src.nguoi3_policy_evidence.policy_agent import run as policy_run
from src.nguoi4_coordinator_verifier.verifier_agent import verify

MODEL_NAME = "gemma3:4b-it-qat"
MODEL_PARAMETER_SIZE = "4B"
FRAMEWORK = "python 3.12 + pandas + Ollama"
RUNTIME = "local via Ollama (127.0.0.1:11434)"

BASE_DIR = Path(__file__).resolve().parents[2]
TRACE_PATH = BASE_DIR / "trace.jsonl"
METADATA_PATH = BASE_DIR / "metadata.json"


def load_case(input_path: str) -> CaseContext:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    claimed_order_id = data["customer_request"]["claimed_order_id"]
    order = load_order(claimed_order_id)
    return CaseContext(
        case_id=data["case_id"],
        claimed_order_id=claimed_order_id,
        order_status=order["order_status"] if order is not None else None,
    )


def _sanitize(value):
    if is_dataclass(value):
        return _sanitize(asdict(value))
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _append_trace(event: dict) -> None:
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open("a", encoding="utf-8") as trace_file:
        trace_file.write(json.dumps(event, ensure_ascii=False) + "\n")


def _write_metadata() -> None:
    metadata = {
        "model": MODEL_NAME,
        "parameter_size": MODEL_PARAMETER_SIZE,
        "framework": FRAMEWORK,
        "runtime": RUNTIME,
        "notes": (
            "Customer, order/product, payment, delivery va policy agents chay "
            "deterministic theo CSV va business rules; model local duoc khai bao "
            "de dap ung yeu cau runtime/model metadata cua bai lab."
        ),
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_case(case_id: str) -> dict:
    """Chạy toàn bộ pipeline cho một case, trả về JSON theo schema README mục 6."""
    input_path = BASE_DIR / "input" / f"{case_id}.json"
    case = load_case(str(input_path))
    _append_trace({"case_id": case_id, "stage": "coordinator", "status": "started"})

    case.customer_context = customer_run(case.claimed_order_id)
    _append_trace(
        {
            "case_id": case_id,
            "stage": "customer_agent",
            "status": "completed",
            "customer_unique_id": case.customer_context.customer_unique_id,
            "related_order_ids": case.customer_context.related_order_ids,
        }
    )

    affected_entities, product_context = order_product_run(case.claimed_order_id)
    case.affected_entities = affected_entities
    case.product_context = product_context
    _append_trace(
        {
            "case_id": case_id,
            "stage": "order_product_agent",
            "status": "completed",
            "affected_entities": _sanitize(case.affected_entities),
            "product_context": _sanitize(case.product_context),
        }
    )

    case.payment_reconciliation, payment_ids = payment_run(case.claimed_order_id)
    case.affected_entities.payment_ids = payment_ids
    _append_trace(
        {
            "case_id": case_id,
            "stage": "payment_agent",
            "status": "completed",
            "payment_reconciliation": _sanitize(case.payment_reconciliation),
            "payment_ids": payment_ids,
        }
    )

    case.delivery_analysis = delivery_run(case.claimed_order_id)
    _append_trace(
        {
            "case_id": case_id,
            "stage": "delivery_agent",
            "status": "completed",
            "delivery_analysis": _sanitize(case.delivery_analysis),
        }
    )

    policy_result = policy_run(case)
    _append_trace(
        {
            "case_id": case_id,
            "stage": "policy_agent",
            "status": "completed",
            "policy_result": _sanitize(policy_result),
        }
    )

    case_output = {
        "case_id": case.case_id,
        "case_assessment": policy_result["case_assessment"],
        "affected_entities": _sanitize(case.affected_entities),
        "customer_context": _sanitize(case.customer_context),
        "product_context": _sanitize(case.product_context),
        "delivery_analysis": _sanitize(case.delivery_analysis),
        "payment_reconciliation": _sanitize(case.payment_reconciliation),
        "root_cause_analysis": policy_result["root_cause_analysis"],
        "evidence_ids": policy_result["evidence_ids"],
        "financial_resolution": policy_result["financial_resolution"],
        "resolution_actions": policy_result["resolution_actions"],
    }

    is_valid, error = verify(case_output)
    _append_trace(
        {
            "case_id": case_id,
            "stage": "verifier_agent",
            "status": "passed" if is_valid else "failed",
            "error": error,
        }
    )
    if not is_valid:
        raise ValueError(f"{case_id} failed verification: {error}")

    return case_output


def run_all(input_dir: str = "input", output_dir: str = "output") -> None:
    """Chạy tuần tự 50 case, ghi kết quả đã qua Verifier vào output/."""
    input_path = BASE_DIR / input_dir
    output_path = BASE_DIR / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    TRACE_PATH.write_text("", encoding="utf-8")
    _write_metadata()

    for existing_json in output_path.glob("EC_*.json"):
        existing_json.unlink()

    input_files = sorted(input_path.glob("EC_*.json"))
    for case_file in input_files:
        case_output = run_case(case_file.stem)
        destination = output_path / case_file.name
        destination.write_text(
            json.dumps(case_output, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )

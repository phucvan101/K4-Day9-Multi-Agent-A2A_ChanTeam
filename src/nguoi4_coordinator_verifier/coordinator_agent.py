"""Coordinator Agent — sở hữu: Người 4.

Nhận input/EC_xxx.json, điều phối Customer/Order&Product/Payment/Delivery Agent,
gộp kết quả gửi Policy Agent, rồi gửi qua Verifier trước khi ghi output/.
"""

from src.common.schema import CaseContext


def load_case(input_path: str) -> CaseContext:
    raise NotImplementedError


def run_case(case_id: str) -> dict:
    """Chạy toàn bộ pipeline cho một case, trả về JSON theo schema README mục 6."""
    raise NotImplementedError


def run_all(input_dir: str = "input", output_dir: str = "output") -> None:
    """Chạy tuần tự 50 case, ghi kết quả đã qua Verifier vào output/."""
    raise NotImplementedError

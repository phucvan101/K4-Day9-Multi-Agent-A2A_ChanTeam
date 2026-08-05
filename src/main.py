"""Entry point — chạy Coordinator cho toàn bộ 50 case trong input/."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.nguoi4_coordinator_verifier.coordinator_agent import run_all

if __name__ == "__main__":
    run_all()

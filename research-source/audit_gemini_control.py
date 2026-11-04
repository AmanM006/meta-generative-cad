"""Audit the partial Gemini comparator without requiring its API key."""
import hashlib
import json
from pathlib import Path

from benchmark_engineering_intent import score, screen
from engineering_intent import validate_model_interpretation
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent


def audit():
    frozen = json.loads((ROOT / "fresh_evidence/intent_spec_confirmatory_frozen.json").read_text())
    ledger = json.loads((ROOT / "fresh_evidence/intent_spec_gemini_control_v2.json").read_text())
    assert digest({k: v for k, v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    assert ledger["frozen_sha256"] == frozen["sha256"]
    for i, receipt in enumerate(ledger["receipts"]):
        assert digest(receipt["request"]) == receipt["request_sha256"], f"request hash {i}"
        assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"], f"response hash {i}"
    correct = 0
    physics_count = 0
    by_id = {c["id"]: c for c in frozen["held_out"]}
    for id, row in ledger["results"].items():
        case = by_id[id]
        receipt = ledger["receipts"][row["receipt_index"]]
        assert case["request"] in receipt["request"]["contents"][0]["parts"][0]["text"]
        try:
            candidate = validate_model_interpretation(case["request"], json.loads(receipt["response"].strip().removeprefix("```json").removesuffix("```").strip()))
        except (ValueError, TypeError):
            candidate = None
        assert candidate == row["candidate"], f"candidate binding {id}"
        assert score(candidate, case["reference"]) == row["score"], f"score {id}"
        expected_screen = screen(candidate, case["request"])
        assert expected_screen["status"] == row["physical_screen"]["status"], f"screen {id}"
        if expected_screen["status"] == "screened":
            stored = row["physical_screen"]["physics"]
            rerun = evaluate(stored["proposal"], expected_screen["task"])
            assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"], f"physics {id}"
            physics_count += 1
        correct += int(row["score"]["complete_correct"])
    return {"status": "PASS", "completed_cases": len(ledger["results"]), "planned_cases": len(frozen["held_out"]),
            "complete_correct": correct, "receipts_verified": len(ledger["receipts"]),
            "physics_recomputed": physics_count,
            "list_price_estimate_usd": sum(r["list_price_estimate_usd"] for r in ledger["receipts"]),
            "actual_billed_cost_usd": "UNKNOWN", "stop_reason": "HTTP_429_QUOTA"}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))

"""Verify the partial matched Gemini control and preserve the quota failure."""
import hashlib
import json
from pathlib import Path

from open_ended_structural_discovery_engine import digest
from run_clarification_20 import metric, normalize

ROOT = Path(__file__).resolve().parent


def main():
    frozen = json.loads((ROOT/"fresh_evidence/clarification_20_frozen.json").read_text())
    ledger = json.loads((ROOT/"fresh_evidence/clarification_20_gemini_control.json").read_text())
    assert ledger["frozen_sha256"] == frozen["sha256"]
    assert digest({k:v for k,v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    cases = {x["id"]: x for x in frozen["cases"]}
    assert len(ledger["results"]) == len(ledger["receipts"])
    for receipt in ledger["receipts"]:
        ident = receipt["case_id"]
        assert digest(receipt["request"]) == receipt["request_sha256"]
        assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"]
        assert cases[ident]["request"] in receipt["request"]["contents"][0]["parts"][0]["text"]
        row = ledger["results"][ident]
        assert ledger["receipts"][row["receipt_index"]] == receipt
        try:
            candidate, failure = normalize(receipt["response"]), None
        except (ValueError, TypeError, KeyError) as exc:
            candidate, failure = None, str(exc)
        assert candidate == row["candidate"] and failure == row["validation_failure"]
        assert metric(candidate, cases[ident]["reference"]) == row["score"]
    assert abs(sum(x["estimated_cost_usd"] for x in ledger["receipts"])-ledger["estimated_new_usd"]) < 1e-10
    assert ledger["status"] == "STOPPED_HTTP_429" and ledger["failures"][-1]["http_status"] == 429
    assert ledger["failures"][-1]["case_id"] not in ledger["results"]
    result = {"status": "PASS", "completed_cases": len(ledger["results"]),
              "planned_cases": len(cases), "fully_correct_completed": sum(r["score"]["full_case"] for r in ledger["results"].values()),
              "quota_stop_case": ledger["failures"][-1]["case_id"],
              "estimated_new_usd": ledger["estimated_new_usd"], "actual_billed_cost_usd": "UNKNOWN"}
    (ROOT/"fresh_evidence/clarification_20_gemini_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

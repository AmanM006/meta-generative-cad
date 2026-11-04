"""Replay the single 12-case revised-rules versus Muse transfer comparison."""
import hashlib
import json
from pathlib import Path

from audit_clarification_20 import interval
from open_ended_structural_discovery_engine import digest
from run_clarification_20 import metric, normalize
from run_clarification_transfer import deterministic

ROOT = Path(__file__).resolve().parent


def main():
    frozen = json.loads((ROOT/"fresh_evidence/clarification_transfer_12_frozen.json").read_text())
    ledger = json.loads((ROOT/"fresh_evidence/clarification_transfer_12_results.json").read_text())
    assert digest({k:v for k,v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    assert ledger["status"] == "COMPLETE" and ledger["frozen_sha256"] == frozen["sha256"]
    assert len(frozen["cases"]) == 12 and len(ledger["receipts"]) == 12 and len(ledger["results"]) == 24
    by_id = {x["id"]: x for x in frozen["cases"]}
    for ident, case in by_id.items():
        fixed = ledger["results"][ident+"/revised_deterministic"]
        assert fixed["candidate"] == deterministic(case["request"])
        assert fixed["score"] == metric(fixed["candidate"], case["reference"])
        model = ledger["results"][ident+"/muse_cold"]
        receipt = ledger["receipts"][model["receipt_index"]]
        assert digest(receipt["request"]) == receipt["request_sha256"]
        assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"]
        assert case["request"] in receipt["request"]["messages"][0]["content"]
        try:
            candidate, failure = normalize(receipt["response"]), None
        except (ValueError, TypeError, KeyError) as exc:
            candidate, failure = None, str(exc)
        assert candidate == model["candidate"] and failure == model["validation_failure"]
        assert model["score"] == metric(candidate, case["reference"])
    cost = sum(x["estimated_cost_usd"] for x in ledger["receipts"])
    assert abs(cost-ledger["estimated_new_meta_usd"]) < 1e-10
    fixed = [int(ledger["results"][ident+"/revised_deterministic"]["score"]["full_case"]) for ident in by_id]
    muse = [int(ledger["results"][ident+"/muse_cold"]["score"]["full_case"]) for ident in by_id]
    delta = [a-b for a,b in zip(muse,fixed)]
    result = {"status": "PASS", "frozen_sha256": frozen["sha256"], "cases": len(by_id),
              "receipt_count": len(ledger["receipts"]), "estimated_new_meta_usd": cost,
              "actual_billed_cost_usd": "UNKNOWN",
              "muse_full": sum(muse), "revised_rules_full": sum(fixed),
              "muse_correct_decisions": sum(ledger["results"][ident+"/muse_cold"]["score"]["decision_correct"] for ident in by_id),
              "rules_correct_decisions": sum(ledger["results"][ident+"/revised_deterministic"]["score"]["decision_correct"] for ident in by_id),
              "paired_delta_muse_minus_rules": sum(delta)/len(delta),
              "paired_bootstrap_95pct": interval(delta),
              "muse_only_wins": sum(x==1 for x in delta), "rules_only_wins": sum(x==-1 for x in delta),
              "limits": ["Project-authored tasks", "Small 12-case transfer set",
                         "No complete general-LLM control", "No human rating of question usefulness"]}
    (ROOT/"fresh_evidence/clarification_transfer_12_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

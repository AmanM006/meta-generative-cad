"""Independent replay of clarification responses, scores, and paired intervals."""
import hashlib
import json
import random
from pathlib import Path

from open_ended_structural_discovery_engine import digest
from run_clarification_20 import ARM_ORDER, deterministic, metric, normalize

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/clarification_20_frozen.json"
LEDGER = ROOT / "fresh_evidence/clarification_20_results.json"
OUT = ROOT / "fresh_evidence/clarification_20_audit.json"


def interval(differences, seed=20261104, draws=10000):
    rng = random.Random(seed)
    n = len(differences)
    means = sorted(sum(differences[rng.randrange(n)] for _ in range(n))/n for _ in range(draws))
    return [means[int(.025*draws)], means[int(.975*draws)]]


def audit(frozen_path=FROZEN, ledger_path=LEDGER, frozen_data=None, ledger_data=None):
    frozen = frozen_data if frozen_data is not None else json.loads(Path(frozen_path).read_text())
    ledger = ledger_data if ledger_data is not None else json.loads(Path(ledger_path).read_text())
    assert digest({k:v for k,v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    assert ledger["frozen_sha256"] == frozen["sha256"]
    assert ledger["status"] == "COMPLETE"
    cases = {case["id"]: case for case in frozen["cases"]}
    assert len(cases) == 20 and len(ledger["results"]) == 20*len(ARM_ORDER)
    used = set()
    for ident, row in ledger["results"].items():
        case_id, arm = ident.split("/")
        assert case_id in cases and arm in ARM_ORDER
        if arm == "deterministic":
            assert row["receipt_index"] is None
            candidate = deterministic(cases[case_id]["request"])
            failure = None
        else:
            index = row["receipt_index"]
            assert isinstance(index, int) and 0 <= index < len(ledger["receipts"])
            assert index not in used
            used.add(index)
            receipt = ledger["receipts"][index]
            assert digest(receipt["request"]) == receipt["request_sha256"]
            assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"]
            assert cases[case_id]["request"] in receipt["request"]["messages"][0]["content"]
            try:
                candidate, failure = normalize(receipt["response"]), None
            except (ValueError, TypeError, KeyError) as exc:
                candidate, failure = None, str(exc)
        assert row["candidate"] == candidate and row["validation_failure"] == failure
        assert row["score"] == metric(candidate, cases[case_id]["reference"]), ident
    assert len(used) == len(ledger["receipts"]) == 60
    cost = sum(receipt["estimated_cost_usd"] for receipt in ledger["receipts"])
    assert abs(cost-ledger["new_estimated_cost_usd"]) < 1e-10
    summary = {}
    for arm in ARM_ORDER:
        scores = [ledger["results"][case_id+"/"+arm]["score"] for case_id in cases]
        summary[arm] = {"full_cases": sum(x["full_case"] for x in scores),
                        "decisions": sum(x["decision_correct"] for x in scores),
                        "fields": sum(x["fields_correct"] for x in scores),
                        "question_fields": sum(x["question_field_correct"] for x in scores),
                        "unsafe_assumptions": sum(x["unsafe_assumptions"] for x in scores),
                        "invalid_responses": sum(ledger["results"][case_id+"/"+arm]["candidate"] is None for case_id in cases)}
    paired = {}
    cold = [int(ledger["results"][case_id+"/muse_cold"]["score"]["full_case"]) for case_id in cases]
    for arm in ("deterministic", "muse_raw_memory", "muse_validated_memory"):
        other = [int(ledger["results"][case_id+"/"+arm]["score"]["full_case"]) for case_id in cases]
        delta = [a-b for a,b in zip(cold,other)]
        paired["muse_cold_minus_"+arm] = {"mean_delta": sum(delta)/len(delta),
                                          "bootstrap_95pct": interval(delta),
                                          "cold_only_wins": sum(x==1 for x in delta),
                                          "other_only_wins": sum(x==-1 for x in delta)}
    return {"status": "PASS", "frozen_sha256": frozen["sha256"],
            "cases": len(cases), "receipts": len(ledger["receipts"]),
            "estimated_new_meta_usd": cost, "actual_billed_cost_usd": "UNKNOWN",
            "summary": summary, "paired": paired,
            "limits": ["Project-authored task set", "No independent human question-quality rating",
                       "Gemini matched control incomplete", "No downstream physics comparison in this audit"]}


if __name__ == "__main__":
    result = audit()
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

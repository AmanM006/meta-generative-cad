"""Recompute the frozen R9 comparison from saved, inspectable case records."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "fresh_evidence"


def main():
    protocol_bytes = (ROOT / "r9_matched_protocol.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    task_hash = hashlib.sha256((ROOT / "r9_frozen_tasks.json").read_bytes()).hexdigest()
    assert task_hash == protocol["task_set_sha256"]
    protocol_hash = hashlib.sha256(protocol_bytes).hexdigest()
    arms = {}
    for arm in "BCDE":
        data = json.loads((ROOT / f"r9_arm_{arm}.json").read_text())
        assert data["frozen_sha256"] == task_hash
        assert data["protocol_sha256"] == protocol_hash
        assert list(data["cases"]) == protocol["cases"]
        records = []
        for ident, case in data["cases"].items():
            if arm == "E":
                records.append({"id": ident, "action": case["action"],
                                "repair_pass": case["robust_before_fallback"],
                                "final_pass": case["final_robust"], "model_calls": 0})
                continue
            raw = case["raw_job"]
            summary = case["summary"]
            receipts = raw.get("receipts", [])
            assert summary["model_calls_with_receipts"] == len(receipts)
            assert summary["prompt_tokens"] == sum(r["prompt_tokens"] for r in receipts)
            assert summary["completion_tokens"] == sum(r["completion_tokens"] for r in receipts)
            assert abs(summary["estimated_cost_usd"] - sum(r["estimated_cost_usd"] for r in receipts)) < 1e-10
            assert summary["all_six_fields_correct"] and summary["final_robust"]
            repair = raw.get("repair_attempt") or {}
            if summary["selection_source"] == "muse_directed_proposal_independently_verified":
                assert repair["verdict"] == "robust_beam_pass"
                assert repair["candidate"]["fine"]["feasible"]
                assert all(c["result"]["feasible"] for c in repair["candidate"]["joint_corners"])
            records.append({"id": ident, "action": summary["repair_action"],
                            "repair_pass": summary["robust_before_fallback"],
                            "final_pass": summary["final_robust"],
                            "prediction_correct": summary["prediction_both_correct"],
                            "model_calls": len(receipts),
                            "estimated_cost_usd": summary["estimated_cost_usd"],
                            "selection_source": summary["selection_source"]})
        arms[arm] = {"repair_passes": sum(x["repair_pass"] for x in records),
                     "final_passes": sum(x["final_pass"] for x in records),
                     "model_calls_with_receipts": sum(x["model_calls"] for x in records),
                     "estimated_cost_usd": sum(x.get("estimated_cost_usd", 0) for x in records),
                     "cases": records}
    result = {"task_set_sha256": task_hash, "protocol_sha256": protocol_hash,
              "scope": protocol["disclosure"],
              "caveat": "API costs are estimates; no billed invoice. Compiler-rejected corners have no FEA direction score. The full deterministic sweep passes all five cases.",
              "arms": arms}
    (ROOT / "r9_matched_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({a: {k: v for k, v in d.items() if k != "cases"}
                      for a, d in arms.items()}, indent=2))


if __name__ == "__main__":
    main()

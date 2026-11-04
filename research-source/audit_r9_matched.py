"""Recompute the frozen R9 comparison from saved, inspectable case records."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "fresh_evidence"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def audit_solver_result(result, task):
    assert result["proposal_sha256"] == digest(result["proposal"])
    if "gates" not in result:
        assert result["feasible"] is False
        return
    gates = result["gates"]
    assert gates["stroke"] == (result["stroke_mm"] >= task["stroke_min_mm"])
    assert gates["absolute_drift"] == (result["absolute_drift_mm"] <= task["drift_max_mm"])
    assert gates["stress"] == (result["stress_mpa"] <= task["stress_max_mpa"])
    assert gates["tangent_stability"] == (result["tangent_min_eigenvalue"] > 0)
    assert result["feasible"] == all(gates.values())


def main(root=ROOT, write=True):
    protocol_bytes = (root / "r9_matched_protocol.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    task_hash = hashlib.sha256((root / "r9_frozen_tasks.json").read_bytes()).hexdigest()
    assert task_hash == protocol["task_set_sha256"]
    protocol_hash = hashlib.sha256(protocol_bytes).hexdigest()
    arms = {}
    for arm in "BCDE":
        data = json.loads((root / f"r9_arm_{arm}.json").read_text())
        assert data["frozen_sha256"] == task_hash
        assert data["protocol_sha256"] == protocol_hash
        assert list(data["cases"]) == protocol["cases"]
        records = []
        for ident, case in data["cases"].items():
            if arm == "E":
                task = json.loads((root / "r9_generalization_results.json").read_text())["cases"][ident]["solver_task"]
                candidate = case["measured"]["candidate"]
                for item in (candidate["coarse"], candidate["fine"]):
                    if item is not None:
                        audit_solver_result(item, task)
                for corner in candidate["joint_corners"]:
                    audit_solver_result(corner["result"], task)
                records.append({"id": ident, "action": case["action"],
                                "repair_pass": case["robust_before_fallback"],
                                "final_pass": case["final_robust"], "model_calls": 0})
                continue
            raw = case["raw_job"]
            task = raw["solver_task"]
            summary = case["summary"]
            receipts = raw.get("receipts", [])
            assert summary["model_calls_with_receipts"] == len(receipts)
            assert summary["prompt_tokens"] == sum(r["prompt_tokens"] for r in receipts)
            assert summary["completion_tokens"] == sum(r["completion_tokens"] for r in receipts)
            assert abs(summary["estimated_cost_usd"] - sum(r["estimated_cost_usd"] for r in receipts)) < 1e-10
            assert summary["all_six_fields_correct"] and summary["final_robust"]
            for trial in raw.get("trials", []):
                for item in (trial["coarse"], trial.get("fine")):
                    if item is not None:
                        audit_solver_result(item, task)
                for corner in trial.get("joint_corners", []):
                    audit_solver_result(corner["result"], task)
            repair = raw.get("repair_attempt") or {}
            if repair.get("candidate"):
                candidate = repair["candidate"]
                for item in (candidate["coarse"], candidate["fine"]):
                    audit_solver_result(item, task)
                for corner in candidate["joint_corners"]:
                    audit_solver_result(corner["result"], task)
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
    if write:
        (root / "r9_matched_audit.json").write_text(json.dumps(result, indent=2))
        print(json.dumps({a: {k: v for k, v in d.items() if k != "cases"}
                          for a, d in arms.items()}, indent=2))
    return result


if __name__ == "__main__":
    main()

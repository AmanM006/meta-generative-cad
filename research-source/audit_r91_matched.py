"""Recompute R9.1 physical, receipt, and paired-decision evidence."""
import hashlib
import json
import math
from pathlib import Path

from scipy.stats import binomtest

from audit_r9_matched import audit_solver_result, digest
from r9_repair_policy import failure_metrics, parse_repair
from run_r91_matched import memory_context

ROOT = Path(__file__).resolve().parent / "fresh_evidence"


def wilson(success, total):
    if not total:
        return [0, 1]
    z = 1.9599639845
    p = success / total
    den = 1 + z*z/total
    center = (p + z*z/(2*total)) / den
    radius = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / den
    return [center-radius, center+radius]


def audit_candidate(measured, task):
    candidate = measured["candidate"]
    for result in (candidate["coarse"], candidate["fine"], measured["measured_failed_scenario_after"]):
        if result:
            audit_solver_result(result, task)
    for corner in candidate["joint_corners"]:
        audit_solver_result(corner["result"], task)
    assert (measured["verdict"] == "robust_beam_pass") == (
        bool(candidate["fine"] and candidate["fine"]["feasible"])
        and len(candidate["joint_corners"]) == 4
        and all(x["result"]["feasible"] for x in candidate["joint_corners"]))
    values = [x["result"] for x in candidate["joint_corners"] if all(
        field in x["result"] for field in ("stroke_mm", "absolute_drift_mm", "stress_mpa"))]
    return {"stroke_margin_mm": min((x["stroke_mm"] - task["stroke_min_mm"] for x in values), default=None),
            "drift_margin_mm": min((task["drift_max_mm"] - x["absolute_drift_mm"] for x in values), default=None),
            "stress_margin_mpa": min((task["stress_max_mpa"] - x["stress_mpa"] for x in values), default=None)}


def audit_receipt(record):
    receipt = record.get("model_receipt")
    if not receipt:
        return 0, 0.0
    assert receipt["request_sha256"] == digest(receipt["request"])
    assert receipt["response_sha256"] == hashlib.sha256(receipt["response"].encode()).hexdigest()
    assert receipt["response"] == record["model_raw"]
    assert receipt["request"]["messages"][0]["content"] == record["model_prompt"]
    assert abs(receipt["estimated_cost_usd"] -
               (receipt["prompt_tokens"]*.20 + receipt["completion_tokens"]*.80)/1e6) < 1e-12
    return 1, receipt["estimated_cost_usd"]


def validate_significance_claim(comparisons, comparison, claimed_significant):
    actual = comparisons[comparison]["exact_mcnemar_p"] < .05
    if claimed_significant != actual:
        raise AssertionError("Significance claim conflicts with exact paired test")


def main(root=ROOT, write=True):
    tasks_bytes = (root / "r91_frozen_tasks.json").read_bytes()
    protocol_bytes = (root / "r91_frozen_protocol.json").read_bytes()
    task_hash = hashlib.sha256(tasks_bytes).hexdigest()
    protocol_hash = hashlib.sha256(protocol_bytes).hexdigest()
    tasks = json.loads(tasks_bytes)["cases"]
    protocol = json.loads(protocol_bytes)
    assert protocol["task_set_sha256"] == task_hash
    baselines = json.loads((root / "r91_baselines.json").read_text())
    assert baselines["task_sha256"] == task_hash and baselines["protocol_sha256"] == protocol_hash
    for case in tasks:
        baseline = baselines["cases"][case["id"]]
        if baseline["status"] == "abstained_before_model":
            assert case["status"] == "unsupported_material_control"
            continue
        task = baseline["solver_task"]
        audit_solver_result(baseline["nominal_fine"], task)
        for corner in baseline["joint_corners"]:
            audit_solver_result(corner["result"], task)
        if baseline["failed"]:
            assert not baseline["failed"]["result"]["feasible"]
            assert failure_metrics(baseline["failed"]["result"], baseline["failed"]["task"])["failed_gates"]
    arms = {}
    for arm in "ABCDE":
        data = json.loads((root / f"r91_arm_{arm}.json").read_text())
        assert data["task_sha256"] == task_hash and data["protocol_sha256"] == protocol_hash
        assert list(data["cases"]) == [x["id"] for x in tasks]
        rows = []
        for case in tasks:
            ident = case["id"]
            baseline = baselines["cases"][ident]
            record = data["cases"][ident]
            row = {"id": ident, "baseline_status": baseline["status"],
                   "action": record["action"], "robust": record["one_step_robust"],
                   "status": record["status"], "fea_evaluations": record["fea_evaluations"],
                   "duration_s": record["duration_s"], "model_calls": 0,
                   "estimated_cost_usd": 0.0, "prediction_both_correct": record.get("prediction_both_correct")}
            if baseline["status"] == "repair_needed":
                task = baseline["solver_task"]
                if arm == "E":
                    assert len(record["attempts"]) == 3
                    assert [x["action"] for x in record["attempts"]] == protocol["actions"]
                    margins = [audit_candidate(x["measured"], task) for x in record["attempts"]]
                    passes = [x for x in record["attempts"] if x["measured"]["verdict"] == "robust_beam_pass"]
                    assert record["one_step_robust"] == bool(passes)
                    assert record["action"] == (passes[0]["action"] if passes else None)
                    row["worst_margins"] = margins[[x["action"] for x in record["attempts"]].index(record["action"])] if passes else None
                else:
                    if record.get("measured"):
                        row["worst_margins"] = audit_candidate(record["measured"], task)
                        assert record["one_step_robust"] == (record["measured"]["verdict"] == "robust_beam_pass")
                    if arm in "BCD":
                        row["model_calls"], row["estimated_cost_usd"] = audit_receipt(record)
                        assert row["model_calls"] == 1, "Every repair-needed model arm needs a receipt"
                        assert record["historical_context"] == memory_context(case["constraints"]["material"], arm)
                        if record.get("choice"):
                            failure = failure_metrics(baseline["failed"]["result"], baseline["failed"]["task"])
                            assert parse_repair(record["model_raw"], failure["failed_gates"]) == record["choice"]
            else:
                assert record["action"] is None and record["model_receipt"] is None
            rows.append(row)
        physical = [x for x in rows if x["baseline_status"] == "repair_needed"]
        arms[arm] = {"repair_passes": sum(x["robust"] for x in physical),
                     "repair_cases": len(physical),
                     "wilson_95": wilson(sum(x["robust"] for x in physical), len(physical)),
                     "model_calls_with_receipts": sum(x["model_calls"] for x in rows),
                     "estimated_cost_usd": sum(x["estimated_cost_usd"] for x in rows),
                     "cases": rows}
    comparisons = {}
    d = {x["id"]: x for x in arms["D"]["cases"]}
    for comparator in "ABCE":
        other = {x["id"]: x for x in arms[comparator]["cases"]}
        ids = [x["id"] for x in arms["D"]["cases"] if x["baseline_status"] == "repair_needed"]
        d_only = sum(d[i]["robust"] and not other[i]["robust"] for i in ids)
        other_only = sum(other[i]["robust"] and not d[i]["robust"] for i in ids)
        discordant = d_only + other_only
        comparisons["D_vs_" + comparator] = {"D_only": d_only, "other_only": other_only,
            "exact_mcnemar_p": binomtest(d_only, discordant, .5).pvalue if discordant else 1.0,
            "paired_risk_difference": (d_only-other_only)/len(ids)}
    result = {"task_sha256": task_hash, "protocol_sha256": protocol_hash,
              "scope": "Project-authored frozen transfer set; fixed graph family; no external blind test",
              "arms": arms, "paired_comparisons": comparisons,
              "warning": "No statistical superiority claim from nine repair-needed tasks. Already-robust cases and unsupported control are reported separately."}
    controls_path = root / "r91_negative_controls.json"
    if controls_path.exists():
        controls = json.loads(controls_path.read_text())
        assert controls["task_sha256"] == task_hash and controls["protocol_sha256"] == protocol_hash
        assert set(controls["cases"]) == {f"{ident}/{variant}" for ident in protocol["negative_controls"]["cases"]
                                         for variant in protocol["negative_controls"]["variants"]}
        control_rows = []
        for name, record in controls["cases"].items():
            ident, variant = name.split("/", 1)
            case = next(x for x in tasks if x["id"] == ident)
            baseline = baselines["cases"][ident]
            if baseline["status"] == "repair_needed":
                calls, cost = audit_receipt(record)
                assert record["historical_context"] == memory_context(case["constraints"]["material"], "D", variant)
                if record.get("measured"):
                    audit_candidate(record["measured"], baseline["solver_task"])
                control_rows.append({"id": name, "action": record["action"],
                                     "robust": record["one_step_robust"],
                                     "model_calls": calls, "estimated_cost_usd": cost})
            else:
                assert record["model_receipt"] is None and record["action"] is None
                control_rows.append({"id": name, "status": baseline["status"], "model_calls": 0})
        result["negative_controls"] = control_rows
    for comparison in comparisons:
        validate_significance_claim(comparisons, comparison, False)
    if write:
        (root / "r91_matched_audit.json").write_text(json.dumps(result, indent=2))
        print(json.dumps({a: {k: v for k, v in x.items() if k != "cases"} for a, x in arms.items()}, indent=2))
        print(json.dumps(comparisons, indent=2))
    return result


if __name__ == "__main__":
    main()

"""Independent checksum, receipt, score, and physics replay for intent benchmark."""
import hashlib
import json
from pathlib import Path

from benchmark_engineering_intent import score, screen
from engineering_intent_clarification_baseline import compile_intent, validate_model_interpretation
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent


def audit(prefix="intent_spec_confirmatory", physics=True):
    frozen = json.loads((ROOT / f"fresh_evidence/{prefix}_frozen.json").read_text())
    study = json.loads((ROOT / f"fresh_evidence/{prefix}_results.json").read_text())
    body = {k: v for k, v in frozen.items() if k != "sha256"}
    assert digest(body) == frozen["sha256"], "frozen task hash"
    assert study["frozen_sha256"] == frozen["sha256"], "result/task binding"
    for i, receipt in enumerate(study["receipts"]):
        assert digest(receipt["request"]) == receipt["request_sha256"], f"request hash {i}"
        assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"], f"response hash {i}"
    assert abs(sum(r["cost_usd"] for r in study["receipts"]) - study["new_cost_usd"]) < 1e-10, "cost sum"
    summary = {arm: {"complete": 0, "decision": 0, "fields": 0, "invalid": 0, "screened": 0,
                     "physics_feasible": 0} for arm in frozen["model_arms"]}
    physics_count = 0
    for case in frozen["held_out"]:
        for arm in frozen["model_arms"]:
            key = case["id"] + "/" + arm
            row = study["results"][key]
            if arm == "deterministic":
                candidate = compile_intent(case["request"])
            else:
                receipt = study["receipts"][row["receipt_index"]]
                assert case["request"] in receipt["request"]["messages"][0]["content"], f"prompt binding {key}"
                try:
                    parsed = json.loads(receipt["response"].strip().removeprefix("```json").removesuffix("```").strip())
                    candidate = validate_model_interpretation(case["request"], parsed)
                except (ValueError, TypeError):
                    candidate = None
            assert candidate == row["candidate"], f"candidate binding {key}"
            metrics = score(candidate, case["reference"])
            assert metrics == row["score"], f"score {key}"
            physical = row["physical_screen"]
            expected_screen = screen(candidate, case["request"])
            assert physical["status"] == expected_screen["status"], f"screen status binding {key}"
            if physical["status"] == "screened":
                assert physical["task"] == expected_screen["task"], f"physical task binding {key}"
                assert physical["physics"]["proposal_sha256"] == expected_screen["physics"]["proposal_sha256"], f"candidate geometry binding {key}"
                assert physical["physics"]["feasible"] == expected_screen["physics"]["feasible"], f"physical verdict binding {key}"
            if physics and physical["status"] == "screened":
                stored = physical["physics"]
                rerun = evaluate(stored["proposal"], physical["task"])
                assert rerun["status"] == stored["status"] and rerun["feasible"] == stored["feasible"], f"physics verdict {key}"
                if rerun["status"] == "evaluated":
                    for name in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                        assert abs(rerun[name]-stored[name]) < 1e-5, f"physics {name} {key}"
                physics_count += 1
            if physics and "fine_mesh_physics" in row:
                fine = row["fine_mesh_physics"]
                assert fine["proposal_sha256"] == physical["physics"]["proposal_sha256"], f"fine/coarse geometry binding {key}"
                rerun = evaluate(fine["proposal"], physical["task"], mesh_density=48)
                assert rerun["status"] == fine["status"] and rerun["feasible"] == fine["feasible"], f"fine mesh {key}"
                for name in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                    assert abs(rerun[name]-fine[name]) < 1e-5, f"fine mesh {name} {key}"
                physics_count += 1
            item = summary[arm]
            item["complete"] += int(metrics["complete_correct"])
            item["decision"] += int(metrics["decision_correct"])
            item["fields"] += metrics["fields_correct"]
            item["invalid"] += int(candidate is None)
            item["screened"] += int(physical["status"] == "screened")
            item["physics_feasible"] += int(bool(physical.get("physics", {}).get("feasible")))
    if physics:
        repair_path = ROOT / "fresh_evidence/intent_c01_drift_repair.json"
        if repair_path.exists():
            repair = json.loads(repair_path.read_text())
            source = study["results"]["C01/muse_cold"]["physical_screen"]["physics"]
            assert repair["source_proposal_sha256"] == source["proposal_sha256"], "repair source binding"
            assert len(repair["coarse"]) == 4, "repair trial budget"
            for stored in repair["coarse"] + [repair["fine_0p9mm"]]:
                proposal = stored["proposal"]
                assert proposal["anchors"] == source["proposal"]["anchors"]
                assert proposal["stages"] == source["proposal"]["stages"]
                for a, b in zip(proposal["connections"], source["proposal"]["connections"]):
                    assert {k:v for k,v in a.items() if k != "thickness"} == {k:v for k,v in b.items() if k != "thickness"}
                rerun = evaluate(proposal, repair["task"], stored["mesh_elements_per_beam"])
                assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"], "repair verdict"
                for name in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                    assert abs(rerun[name]-stored[name]) < 1e-5, f"repair {name}"
                physics_count += 1
        robustness_path = ROOT / "fresh_evidence/intent_c01_robustness.json"
        if robustness_path.exists():
            robust = json.loads(robustness_path.read_text())
            assert robust["source_sha256"] == digest(repair), "robustness source binding"
            assert robust["nominal_proposal_sha256"] == repair["fine_0p9mm"]["proposal_sha256"], "robustness proposal binding"
            for row in robust["mesh_refinement"]:
                stored = row["result"]
                rerun = evaluate(stored["proposal"], repair["task"], row["elements_per_beam"])
                assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
                physics_count += 1
            for row in robust["parameter_sensitivity"]:
                stored = row["result"]
                rerun = evaluate(stored["proposal"], row["task"], mesh_density=48)
                assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
                physics_count += 1
        search_path = ROOT / "fresh_evidence/intent_c01_robust_search.json"
        if search_path.exists():
            search = json.loads(search_path.read_text())
            assert search["status"] == "COMPLETE" and search["source_sha256"] == digest(repair)
            assert search["predeclared_thicknesses_mm"] == [0.9, 1.0, 1.1, 1.2]
            assert len(search["candidates"]) == 4 and len(search["fine_verification"]) == 4
            assert [c["all_pass"] for c in search["candidates"]] == [False, True, False, False]
            for candidate in search["candidates"]:
                assert candidate["proposal_sha256"] == digest(candidate["proposal"])
                assert len(candidate["checks"]) == 4
                assert candidate["all_pass"] == all(x["result"]["feasible"] for x in candidate["checks"])
                for row in candidate["checks"]:
                    stored = row["result"]
                    rerun = evaluate(stored["proposal"], row["task"], mesh_density=16)
                    assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
                    for name in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                        assert abs(rerun[name]-stored[name]) < 1e-5
                    physics_count += 1
            for row in search["fine_verification"]:
                stored = row["result"]
                rerun = evaluate(stored["proposal"], row["task"], mesh_density=48)
                assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
                for name in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                    assert abs(rerun[name]-stored[name]) < 1e-5
                physics_count += 1
            assert search["fine_robust"] == all(x["result"]["feasible"] for x in search["fine_verification"])
    return {"status": "PASS", "task_sha256": frozen["sha256"], "cases": len(frozen["held_out"]),
            "receipt_count": len(study["receipts"]), "new_cost_usd": study["new_cost_usd"],
            "physics_recomputed": physics_count, "summary": summary,
            "general_llm_control": frozen["general_llm_control"]}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))

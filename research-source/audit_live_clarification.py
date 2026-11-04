"""Verify a genuine local Muse call and recompute its complete solver trail."""
import hashlib
import json
from pathlib import Path

from engineering_intent import compile_intent
from open_ended_structural_discovery_engine import digest, evaluate
from run_clarification_20 import normalize

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fresh_evidence/live_clarification_operator_run.json"


def main():
    record = json.loads(SOURCE.read_text())
    assert record["status"] == "BEAM_MODEL_JOINT_PASS_AFTER_DETERMINISTIC_REPAIR"
    assert record["execution"] == "LOCAL_LIVE_MUSE_WITH_SCRIPTED_ANSWER"
    assert len(record["receipts"]) == 1
    receipt = record["receipts"][0]
    assert digest(receipt["request"]) == receipt["request_sha256"]
    assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"]
    assert record["request"] in receipt["request"]["messages"][0]["content"]
    assert normalize(receipt["response"]) == record["interpretation"]
    assert record["answer"]["source"] == "scripted_fixture"
    merged = record["request"] + " force " + record["answer"]["text"]
    assert compile_intent(merged) == record["compiled_specification"]
    assert record["estimated_new_meta_usd"] == receipt["estimated_cost_usd"]
    solver = record["solver"]
    assert [x["thickness_mm"] for x in solver["trials"]] == [.6,.7,.8,.9,1.0]
    count = 0
    for trial in solver["trials"]:
        proposal = trial["coarse"]["proposal"]
        for kind, density in (("coarse", 16), ("fine", 48)):
            stored = trial[kind]
            if stored is None:
                assert kind == "fine" and not trial["coarse"]["feasible"]
                continue
            rerun = evaluate(proposal, solver["task"], mesh_density=density)
            assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
            for field in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                assert abs(rerun[field]-stored[field]) < 1e-5
            count += 1
    assert solver["selected_mm"] == .9 and len(solver["joint_corners"]) == 4
    assert [x["result"]["feasible"] for x in solver["joint_corners"]] == [False,True,True,True]
    assert record["robust_repair"]["selected_mm"] == 1.0
    assert len(record["robust_repair"]["candidates"]) == 1
    assert record["robust_repair"]["candidates"][0]["all_pass"]
    corners = solver["joint_corners"] + record["robust_repair"]["candidates"][0]["checks"]
    for row in corners:
        stored = row["result"]
        rerun = evaluate(stored["proposal"], row["task"], mesh_density=48)
        assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
        for field in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
            assert abs(rerun[field]-stored[field]) < 1e-5
        count += 1
    result = {"status": "PASS", "receipt_count": 1, "physics_recomputed": count,
              "estimated_new_meta_usd": receipt["estimated_cost_usd"],
              "first_nominal_mm": solver["selected_mm"], "robust_repair_mm": record["robust_repair"]["selected_mm"]}
    (ROOT / "fresh_evidence/live_clarification_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

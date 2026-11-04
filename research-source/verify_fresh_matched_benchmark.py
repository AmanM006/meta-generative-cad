"""Recompute every stored candidate verdict from the fresh paired benchmark."""
import json
from pathlib import Path

from neodustria_gp_first_scientist import NeodustriaGPFirstScientist, check_strict_acceptance
from fresh_matched_benchmark import sha

ROOT = Path(__file__).resolve().parent
evidence = json.loads((ROOT / "fresh_evidence" / "matched_benchmark.json").read_text())
tasks = {t["task_id"]: t for t in evidence["tasks"]}
checked = 0
for trial in evidence["results"]:
    task = tasks[trial["task_id"]]
    assert trial["task_sha256"] == sha(task)
    agent = NeodustriaGPFirstScientist(task, seed=trial["seed"], max_budget=trial["max_fea_budget"])
    for row in trial["evaluations"]:
        if "geometry_spec" not in row or "result" not in row:
            assert row["feasible"] is False
            continue
        fresh = agent.eng.evaluate_task_specific(row["geometry_spec"], row["thickness_m"],
                                                 task["Fy_N"], task["req_stroke_mm"],
                                                 task["max_stress_MPa"], max_drift_mm=task["max_parasitic_dx_mm"])
        verdict, reason = check_strict_acceptance(fresh, task)
        assert bool(verdict) == row["feasible"], (trial["task_id"], trial["arm"], row["index"])
        assert reason == row["reason"], (trial["task_id"], trial["arm"], row["index"])
        checked += 1
    assert len(trial["evaluations"]) <= trial["max_fea_budget"]
    assert trial["feasible"] == any(row["feasible"] for row in trial["evaluations"])
print(f"PASS: {checked} candidate FEA verdicts replayed across {len(evidence['results'])} paired trials")

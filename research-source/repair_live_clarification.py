"""Escalate a recorded nominal pass to the next predeclared robust candidate."""
import copy
import json
from pathlib import Path

from open_ended_structural_discovery_engine import evaluate

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fresh_evidence/live_clarification_operator_run.json"
CORNERS = (("low_low", .95, .90), ("low_high", .95, 1.10),
           ("high_low", 1.05, .90), ("high_high", 1.05, 1.10))


def main():
    record = json.loads(SOURCE.read_text())
    assert record["status"] == "BEAM_MODEL_JOINT_FAIL"
    assert record["solver"]["selected_mm"] == .9
    assert "robust_repair" not in record
    task = record["solver"]["task"]
    trials = record["solver"]["trials"]
    candidates = [row for row in trials if row["thickness_mm"] > record["solver"]["selected_mm"]
                  and row["fine"] and row["fine"]["feasible"]]
    repair = {"reason": "First nominally feasible candidate failed a declared joint corner",
              "selection": "first remaining fine-mesh feasible predeclared thickness passing all four joint corners",
              "candidates": [], "selected_mm": None}
    for row in candidates:
        candidate = row["fine"]["proposal"]
        checks = []
        for name, thickness_scale, modulus_scale in CORNERS:
            variant = copy.deepcopy(candidate)
            changed_task = copy.deepcopy(task)
            for edge in variant["connections"]:
                edge["thickness"] *= thickness_scale
            changed_task["material_properties"]["E_pa"] *= modulus_scale
            result = evaluate(variant, changed_task, mesh_density=48)
            checks.append({"name": name, "thickness_scale": thickness_scale,
                           "modulus_scale": modulus_scale, "task": changed_task, "result": result})
            print("REPAIR", row["thickness_mm"], name, result["feasible"], flush=True)
        all_pass = all(x["result"]["feasible"] for x in checks)
        repair["candidates"].append({"thickness_mm": row["thickness_mm"],
                                     "checks": checks, "all_pass": all_pass})
        if all_pass:
            repair["selected_mm"] = row["thickness_mm"]
            break
    record["robust_repair"] = repair
    record["status"] = ("BEAM_MODEL_JOINT_PASS_AFTER_DETERMINISTIC_REPAIR" if repair["selected_mm"] is not None
                        else "NO_ROBUST_CANDIDATE_WITHIN_BUDGET")
    SOURCE.write_text(json.dumps(record, indent=2))
    print("FINAL", record["status"], repair["selected_mm"])


if __name__ == "__main__":
    main()

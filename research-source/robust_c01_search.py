"""Bounded, predeclared C01 thickness search under joint uncertainty."""
import copy
import json
from pathlib import Path

from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fresh_evidence/intent_c01_drift_repair.json"
TARGET = ROOT / "fresh_evidence/intent_c01_robust_search.json"
THICKNESSES_MM = (0.9, 1.0, 1.1, 1.2)
SCENARIOS = (("low_low", 0.95, 0.90), ("low_high", 0.95, 1.10),
             ("high_low", 1.05, 0.90), ("high_high", 1.05, 1.10))


def check(proposal, task, name, thickness_scale, modulus_scale, mesh_density):
    candidate = copy.deepcopy(proposal)
    scenario_task = copy.deepcopy(task)
    for edge in candidate["connections"]:
        edge["thickness"] *= thickness_scale
    scenario_task["material_properties"]["E_pa"] *= modulus_scale
    result = evaluate(candidate, scenario_task, mesh_density=mesh_density)
    return {"scenario": name, "thickness_scale": thickness_scale,
            "modulus_scale": modulus_scale, "task": scenario_task, "result": result}


def main():
    source = json.loads(SOURCE.read_text())
    task = source["task"]
    base = source["fine_0p9mm"]["proposal"]
    record = {"source_sha256": digest(source), "predeclared_thicknesses_mm": THICKNESSES_MM,
              "predeclared_scenarios": SCENARIOS, "coarse_mesh": 16, "fine_mesh": 48,
              "selection": "first candidate passing all four joint scenarios at coarse mesh",
              "scope": "2D nonlinear beam screening; no fabrication or continuum certification",
              "candidates": [], "fine_verification": []}
    winner = None
    for thickness_mm in THICKNESSES_MM:
        candidate = copy.deepcopy(base)
        for edge in candidate["connections"]:
            edge["thickness"] = thickness_mm / 1000
        checks = [check(candidate, task, *scenario, mesh_density=16) for scenario in SCENARIOS]
        all_pass = all(row["result"]["feasible"] for row in checks)
        record["candidates"].append({"thickness_mm": thickness_mm, "proposal": candidate,
                                     "proposal_sha256": digest(candidate), "checks": checks,
                                     "all_pass": all_pass})
        TARGET.write_text(json.dumps(record, indent=2))
        print("COARSE", thickness_mm, all_pass, flush=True)
        if all_pass and winner is None:
            winner = candidate
    if winner is not None:
        for scenario in SCENARIOS:
            row = check(winner, task, *scenario, mesh_density=48)
            record["fine_verification"].append(row)
            TARGET.write_text(json.dumps(record, indent=2))
            print("FINE", scenario[0], row["result"]["feasible"], flush=True)
    record["status"] = "COMPLETE"
    record["fine_robust"] = bool(winner is not None and all(row["result"]["feasible"] for row in record["fine_verification"]))
    TARGET.write_text(json.dumps(record, indent=2))
    print("FINE_ROBUST", record["fine_robust"], flush=True)


if __name__ == "__main__":
    main()

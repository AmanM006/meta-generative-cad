"""Recompute C01 repair across mesh and independent parameter perturbations."""
import copy
import json
from pathlib import Path

from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fresh_evidence/intent_c01_drift_repair.json"
TARGET = ROOT / "fresh_evidence/intent_c01_robustness.json"


def main():
    source = json.loads(SOURCE.read_text())
    task = source["task"]
    proposal = source["fine_0p9mm"]["proposal"]
    record = {"source_sha256": digest(source), "nominal_proposal_sha256": digest(proposal),
              "scope": "Beam-model numerical and one-factor-at-a-time sensitivity only; no continuum or fabricated validation",
              "mesh_refinement": [], "parameter_sensitivity": []}
    for density in (8, 16, 32, 48):
        row = evaluate(proposal, task, mesh_density=density)
        record["mesh_refinement"].append({"elements_per_beam": density, "result": row})
        TARGET.write_text(json.dumps(record, indent=2))
        print("MESH", density, row["feasible"], row.get("stroke_mm"), row.get("absolute_drift_mm"), flush=True)
    for name, thickness_scale, modulus_scale in (
        ("thickness_minus_5pct", .95, 1.0), ("thickness_plus_5pct", 1.05, 1.0),
        ("modulus_minus_10pct", 1.0, .90), ("modulus_plus_10pct", 1.0, 1.10),
        ("combined_low_thickness_low_modulus", .95, .90),
        ("combined_high_thickness_high_modulus", 1.05, 1.10)):
        candidate = copy.deepcopy(proposal)
        changed_task = copy.deepcopy(task)
        for edge in candidate["connections"]:
            edge["thickness"] *= thickness_scale
        changed_task["material_properties"]["E_pa"] *= modulus_scale
        row = evaluate(candidate, changed_task, mesh_density=48)
        record["parameter_sensitivity"].append({"case": name, "thickness_scale": thickness_scale,
                                                "modulus_scale": modulus_scale, "task": changed_task,
                                                "result": row})
        TARGET.write_text(json.dumps(record, indent=2))
        print("SENSITIVITY", name, row["feasible"], row.get("stroke_mm"), row.get("absolute_drift_mm"), flush=True)
    record["status"] = "COMPLETE"
    TARGET.write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

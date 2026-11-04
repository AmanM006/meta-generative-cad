"""Freeze project-authored R9.1 transfer cases before evaluating any of them."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "fresh_evidence"
TASKS = ROOT / "r91_frozen_tasks.json"
PROTOCOL = ROOT / "r91_frozen_protocol.json"

DATA = [
    ("T01", "polypropylene", 2.8, .55, [66, 42], .022, 20, .6),
    ("T02", "polypropylene", 3.6, .78, [72, 46], .026, 22, .6),
    ("T03", "polypropylene", 4.7, 1.05, [80, 52], .029, 24, .7),
    ("T04", "polypropylene", 5.8, 1.20, [88, 58], .034, 27, .8),
    ("T05", "polypropylene", 6.8, 1.35, [96, 64], .040, 30, .8),
    ("T06", "petg", 3.2, .58, [62, 41], .026, 25, .6),
    ("T07", "petg", 4.4, .82, [70, 47], .029, 26, .7),
    ("T08", "petg", 5.7, 1.05, [82, 53], .033, 28, .8),
    ("T09", "petg", 7.1, 1.25, [90, 61], .039, 32, .8),
    ("T10", "petg", 8.4, 1.45, [102, 68], .045, 34, .9),
    ("T11", "polypropylene", 4.5, .90, [78, 50], .005, 22, .7),
]


def main():
    if TASKS.exists() or PROTOCOL.exists():
        raise SystemExit("R9.1 freeze already exists; never overwrite after outcomes")
    cases = [{"id": ident, "status": "supported", "constraints": {
        "material": material, "force_n": force, "stroke_min_mm": stroke,
        "envelope_mm": envelope, "drift_max_mm": drift, "stress_max_mpa": stress},
        "baseline_uniform_thickness_mm": baseline}
        for ident, material, force, stroke, envelope, drift, stress, baseline in DATA]
    cases.append({"id": "T12", "status": "unsupported_material_control", "constraints": {
        "material": "aluminum", "force_n": 5.2, "stroke_min_mm": .9,
        "envelope_mm": [76, 49], "drift_max_mm": .03, "stress_max_mpa": 50},
        "baseline_uniform_thickness_mm": .7})
    tasks = {"title": "R9.1 project-authored transfer cases", "status": "frozen_before_any_T01_to_T12_solver_or_model_outcome",
             "source": "New numeric configurations, not external held-out tasks; all cases retained including failed and unsupported cases",
             "cases": cases}
    TASKS.write_text(json.dumps(tasks, indent=2) + "\n")
    task_hash = hashlib.sha256(TASKS.read_bytes()).hexdigest()
    protocol = {
        "title": "R9.1 bounded matched physical repair decision test",
        "task_set_sha256": task_hash,
        "commit_before_outcomes_required": True,
        "scope": "Fixed scaled two-stage PP/PETG graph; 2D nonlinear beam model; project-authored tasks, no external blind test",
        "solver": {"coarse_mesh_elements_per_beam": 16, "fine_mesh_elements_per_beam": 48,
                   "joint_corners": [["low_low", .95, .90], ["low_high", .95, 1.10],
                                     ["high_low", 1.05, .90], ["high_high", 1.05, 1.10]]},
        "actions": ["uniform_plus_0p1", "outer_plus_0p1", "bridge_plus_0p1"],
        "baseline_rule": "Use the frozen thickness in each case. If nominal fine passes, diagnose the first failed joint corner; otherwise diagnose nominal fine failure. If all corners pass, record already robust and do not make model calls.",
        "arms": {"A": "Predeclared drift->outer, otherwise uniform one-step rule",
                 "B": "Muse with no memory, one action",
                 "C": "Muse with top two material-matched raw R9 records, one action",
                 "D": "Muse with a concise summary of the same measured R9 records and their counterexamples, one action",
                 "E": "Deterministic evaluation of all three allowed actions, larger budget"},
        "historical_memory_source": "Only R9 G01-G05 saved FEA results and actions; retrieval uses material match then fixed G01-G05 order, no R9.1 outcomes",
        "negative_controls": {"cases": ["T03", "T08"], "variants": ["irrelevant_memory", "contradictory_memory"],
                              "purpose": "Sensitivity check; never included in primary paired success rate"},
        "model_ceiling": {"reserved_calls": 48, "estimated_usd": .05},
        "physical_acceptance": "Nominal fine and all four joint corners feasible; record stroke, absolute drift, stress, tangent stability and deformed envelope gates",
        "primary_metric": "Paired one-step robust pass on T01-T11; T12 unsupported abstention is separate",
        "analysis": "Per-task table; exact discordant-pair inference with confidence intervals; no significance claim from tiny sample. No post-outcome task edits or subset selection.",
    }
    PROTOCOL.write_text(json.dumps(protocol, indent=2) + "\n")
    print({"cases": len(cases), "task_sha256": task_hash,
           "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()})


if __name__ == "__main__":
    main()

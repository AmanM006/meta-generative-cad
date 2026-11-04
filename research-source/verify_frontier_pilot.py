"""Recompute all frontier pilot candidates with the current physical gates."""
import json
from pathlib import Path

from open_ended_structural_discovery_engine import digest, evaluate

path = Path(__file__).resolve().parent / "fresh_evidence" / "frontier_open_graph_pilot.json"
pilot = json.loads(path.read_text())
assert digest(pilot["task"]) == pilot["task_sha256"]
reaudit = {"compiler_version": "deformed-envelope-gate-v1", "classical": [], "muse": []}
for arm in ("classical", "muse"):
    for original in pilot[arm]:
        assert digest(original["proposal"]) == original["proposal_sha256"]
        fresh = evaluate(original["proposal"], pilot["task"], original["mesh_elements_per_beam"])
        for metric in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
            if metric in original and metric in fresh:
                assert abs(original[metric]-fresh[metric]) < 1e-6
        reaudit[arm].append(fresh)
pilot["physics_reaudit"] = reaudit
path.write_text(json.dumps(pilot, indent=2))
print("REPLAYED", sum(len(reaudit[a]) for a in reaudit if isinstance(reaudit[a], list)),
      "CLASSICAL_PASS", sum(r["feasible"] for r in reaudit["classical"]),
      "MUSE_PASS", sum(r["feasible"] for r in reaudit["muse"]))

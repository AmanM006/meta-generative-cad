"""Run the precommitted R9.1 baseline designs without model calls."""
import asyncio
import copy
import hashlib
import json
from pathlib import Path

import live_engineering_service as live

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "fresh_evidence/r91_frozen_tasks.json"
PROTOCOL = ROOT / "fresh_evidence/r91_frozen_protocol.json"
OUTPUT = ROOT / "fresh_evidence/r91_baselines.json"


async def main():
    protocol = json.loads(PROTOCOL.read_text())
    assert hashlib.sha256(TASKS.read_bytes()).hexdigest() == protocol["task_set_sha256"]
    data = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {
        "task_sha256": protocol["task_set_sha256"],
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(), "cases": {}}
    assert data["protocol_sha256"] == hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    source = json.loads(live.SOURCE.read_text())["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
    for case in json.loads(TASKS.read_text())["cases"]:
        ident = case["id"]
        if ident in data["cases"]:
            continue
        if case["status"] != "supported":
            try:
                live.preflight_supported(case["constraints"])
            except ValueError as exc:
                data["cases"][ident] = {"status": "abstained_before_model", "reason": str(exc)}
            else:
                raise AssertionError("Frozen unsupported case unexpectedly passed preflight")
        else:
            constraints = case["constraints"]
            live.preflight_supported(constraints)
            spec = {"constraints": constraints, "measured_E_gpa": None}
            task = live.task_for(spec)
            proposal = live.proposal_for_envelope(source, constraints["envelope_mm"])
            for edge in proposal["connections"]:
                edge["thickness"] = case["baseline_uniform_thickness_mm"] / 1000
            fine = await live.evaluate_bounded(proposal, task, 48)
            corners = []
            if fine["feasible"]:
                for name, tscale, escale in live.JOINT_CORNERS:
                    variant = copy.deepcopy(proposal)
                    variant_task = copy.deepcopy(task)
                    for edge in variant["connections"]:
                        edge["thickness"] *= tscale
                    variant_task["material_properties"]["E_pa"] *= escale
                    result = await live.evaluate_bounded(variant, variant_task, 48)
                    corners.append({"name": name, "thickness_scale": tscale,
                                    "modulus_scale": escale, "task": variant_task,
                                    "result": result})
            failed = (next((x for x in corners if not x["result"]["feasible"]), None)
                      if fine["feasible"] else {"name": "nominal", "thickness_scale": 1.0,
                                                "modulus_scale": 1.0, "task": task, "result": fine})
            data["cases"][ident] = {"status": "already_robust" if failed is None else "repair_needed",
                                    "specification": spec, "solver_task": task, "baseline_proposal": proposal,
                                    "nominal_fine": fine, "joint_corners": corners, "failed": failed}
        OUTPUT.write_text(json.dumps(data, indent=2))
        print(ident, data["cases"][ident]["status"], flush=True)


if __name__ == "__main__":
    asyncio.run(main())

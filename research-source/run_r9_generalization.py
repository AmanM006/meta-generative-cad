"""Run the frozen R9 cases through the real bounded beam solver, without API calls."""
import asyncio
import hashlib
import json
import time
from pathlib import Path

from engineering_intent import compile_intent
from live_engineering_service import preflight_supported, run_solver

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/r9_frozen_tasks.json"
OUTPUT = ROOT / "fresh_evidence/r9_generalization_results.json"


async def main():
    frozen_bytes = FROZEN.read_bytes()
    frozen = json.loads(frozen_bytes)
    results = {"frozen_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
               "execution": "fresh_local_nonlinear_beam; no_model_calls", "cases": {}}
    for case in frozen["cases"]:
        ident = case["id"]
        text = case["request"]
        if case.get("answer"):
            text += " force " + case["answer"]
        parsed = compile_intent(text)
        entry = {"request": case["request"], "parsed_decision": parsed["decision"],
                 "parsed_constraints": parsed["constraints"]}
        try:
            preflight_supported(parsed["constraints"], parsed["material_properties"]["measured_E_gpa"])
            if parsed["decision"] in {"contradictory", "unsupported_physics"}:
                entry["screen"] = "blocked_by_independent_gate"
            elif parsed["decision"] != "ready_for_static_beam_screen":
                entry["screen"] = "requires_clarification"
            else:
                job = {"id": "r9-" + ident, "status": "screening", "events": [], "receipts": [],
                       "specification": {"constraints": parsed["constraints"],
                                         "measured_E_gpa": parsed["material_properties"]["measured_E_gpa"]}}
                start = time.perf_counter()
                await run_solver(job)
                entry.update({"screen": job["status"], "verdict": job.get("verdict"),
                              "selected_mm": job.get("selected_mm"),
                              "duration_s": time.perf_counter() - start,
                              "solver_task": job.get("solver_task"),
                              "geometry_source_sha256": job.get("geometry_source_sha256"),
                              "evaluated_geometry_sha256": job.get("evaluated_geometry_sha256"),
                              "geometry_family": job.get("geometry_family"),
                              "trials": job.get("trials", []), "events": job["events"],
                              "error_type": job.get("error")})
        except ValueError as exc:
            entry["screen"] = "blocked_by_supported_domain"
            entry["block_reason"] = str(exc)
        results["cases"][ident] = entry
        OUTPUT.write_text(json.dumps(results, indent=2))
        print(ident, entry["screen"], entry.get("selected_mm"),
              round(entry.get("duration_s", 0), 2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

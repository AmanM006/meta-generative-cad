"""Local live Muse clarification followed by bounded deterministic beam screening.

The public hosted app does not call this command. It is a local operator tool.
"""
import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from engineering_intent import MATERIALS, clarification, compile_intent
from open_ended_structural_discovery_engine import digest, evaluate
from run_clarification_20 import muse, normalize, prompt_for

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "fresh_evidence/live_clarification_operator_run.json"
SOURCE = ROOT / "fresh_evidence/intent_spec_confirmatory_results.json"
PREFIX = {"force_n": "force", "stroke_min_mm": "stroke", "material": "material",
          "envelope_mm": "package", "material_properties": "measured modulus"}
THICKNESSES_MM = (0.6, 0.7, 0.8, 0.9, 1.0)
JOINT_CORNERS = (("low_low", .95, .90), ("low_high", .95, 1.10),
                 ("high_low", 1.05, .90), ("high_high", 1.05, 1.10))


def save(state):
    OUT.write_text(json.dumps(state, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--answer", help="Scripted answer fixture; omit for interactive input")
    args = parser.parse_args()
    if OUT.exists():
        raise SystemExit("Existing operator record would be overwritten; archive it first")
    state = {"created_utc": datetime.now(timezone.utc).isoformat(),
             "execution": "LOCAL_LIVE_MUSE_WITH_SCRIPTED_ANSWER" if args.answer else "LOCAL_LIVE_MUSE_WITH_OPERATOR_ANSWER",
             "request": args.request, "receipts": [], "interpretation": None,
             "answer": None, "compiled_specification": None, "solver": None,
             "status": "STARTED"}
    independent = compile_intent(args.request)
    if independent["decision"] in {"contradictory", "unsupported_physics"}:
        state.update(status="BLOCKED_BY_INDEPENDENT_SAFETY_GATE", independent_gate=independent)
        save(state)
        print(state["status"])
        return
    raw, receipt = muse(prompt_for(args.request, "muse_cold"), state)
    state["receipts"].append(receipt)
    save(state)
    try:
        candidate = normalize(raw)
    except (ValueError, TypeError, KeyError) as exc:
        state.update(status="INVALID_MODEL_OUTPUT", error=str(exc))
        save(state)
        print(state["status"])
        return
    state["interpretation"] = candidate
    save(state)
    if candidate["decision"] == "abstain":
        state["status"] = "MODEL_ABSTAINED"
        save(state)
        print(state["status"])
        return
    if candidate["decision"] == "clarify":
        question = candidate["question"]
        answer = args.answer if args.answer is not None else input(question + "\n> ")
        state["answer"] = {"question": question, "field": candidate["question_field"],
                           "text": answer, "source": "scripted_fixture" if args.answer is not None else "operator_input"}
        merged = args.request + " " + PREFIX[candidate["question_field"]] + " " + answer
    else:
        merged = args.request
    compiled = compile_intent(merged)
    state["compiled_specification"] = compiled
    save(state)
    if compiled["decision"] != "ready_for_static_beam_screen":
        state.update(status="FURTHER_CLARIFICATION_REQUIRED", next_question=clarification(compiled))
        save(state)
        print(state["status"], state["next_question"])
        return
    c = compiled["constraints"]
    if c["drift_max_mm"] is None or c["stress_max_mpa"] is None:
        state.update(status="PHYSICAL_LIMITS_REQUIRED",
                     reason="Explicit drift and stress limits required for this local solver demonstration")
        save(state)
        print(state["status"])
        return
    if c["envelope_mm"] != [75.0, 50.0]:
        state.update(status="TEMPLATE_OUTSIDE_SCOPE",
                     reason="The bounded stored two-stage graph is defined for 75 x 50 mm only")
        save(state)
        print(state["status"])
        return
    source = json.loads(SOURCE.read_text())
    base = source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
    material = dict(MATERIALS[c["material"]], depth_m=.01)
    if compiled["material_properties"]["measured_E_gpa"] is not None:
        material["E_pa"] = compiled["material_properties"]["measured_E_gpa"]*1e9
    task = {"envelope_m": [x/1000 for x in c["envelope_mm"]],
            "material_properties": material, "force_n": c["force_n"],
            "stroke_min_mm": c["stroke_min_mm"], "drift_max_mm": c["drift_max_mm"],
            "stress_max_mpa": c["stress_max_mpa"], "min_flexure_thickness_m": .0006}
    solver = {"task": task, "source_proposal_sha256": digest(base),
              "assumptions": ["Fixed 10 mm depth for stored two-stage beam template",
                              "Nominal tabulated material properties unless measured modulus supplied"],
              "trials": [], "selected_mm": None, "joint_corners": []}
    state["solver"] = solver
    save(state)
    selected = None
    for thickness in THICKNESSES_MM:
        candidate = copy.deepcopy(base)
        for edge in candidate["connections"]:
            edge["thickness"] = thickness/1000
        coarse = evaluate(candidate, task, mesh_density=16)
        fine = evaluate(candidate, task, mesh_density=48) if coarse["feasible"] else None
        solver["trials"].append({"thickness_mm": thickness, "coarse": coarse, "fine": fine})
        if fine and fine["feasible"] and selected is None:
            selected = candidate
            solver["selected_mm"] = thickness
        save(state)
        print("TRIAL", thickness, coarse["feasible"], fine["feasible"] if fine else "not_run", flush=True)
    if selected is None:
        state["status"] = "NO_FEASIBLE_CANDIDATE_WITHIN_BUDGET"
    else:
        for name, thickness_scale, modulus_scale in JOINT_CORNERS:
            candidate = copy.deepcopy(selected)
            variant_task = copy.deepcopy(task)
            for edge in candidate["connections"]:
                edge["thickness"] *= thickness_scale
            variant_task["material_properties"]["E_pa"] *= modulus_scale
            result = evaluate(candidate, variant_task, mesh_density=48)
            solver["joint_corners"].append({"name": name, "task": variant_task,
                                            "thickness_scale": thickness_scale,
                                            "modulus_scale": modulus_scale, "result": result})
            save(state)
            print("JOINT", name, result["feasible"], flush=True)
        state["status"] = ("BEAM_MODEL_JOINT_PASS" if all(x["result"]["feasible"] for x in solver["joint_corners"])
                           else "BEAM_MODEL_JOINT_FAIL")
    state["estimated_new_meta_usd"] = sum(x["estimated_cost_usd"] for x in state["receipts"])
    save(state)
    print("COMPLETE", state["status"], "estimated_meta_usd", state["estimated_new_meta_usd"])


if __name__ == "__main__":
    main()

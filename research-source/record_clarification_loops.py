"""Three scripted clarification demonstrations with actual deterministic beam FEA."""
import copy
import json
from pathlib import Path

from engineering_intent import MATERIALS, compile_intent
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/clarification_20_frozen.json"
STUDY = ROOT / "fresh_evidence/clarification_20_results.json"
SOURCE = ROOT / "fresh_evidence/intent_spec_confirmatory_results.json"
OUT = ROOT / "fresh_evidence/clarification_3_scripted_loops.json"

# Scripted answers are fixtures, not real human conversations. Each explicitly
# supplies numerical limits needed for a meaningful physical decision.
ANSWERS = {
    "Q02": "force 6 N; drift under 0.03 mm; stress under 20 MPa.",
    "Q03": "stroke 1.0 mm; drift under 0.05 mm; stress under 20 MPa.",
    "Q04": "material PETG; drift under 0.03 mm; stress under 30 MPa.",
}
THICKNESSES_MM = (0.6, 0.7, 0.8, 0.9, 1.0)


def main():
    frozen = json.loads(FROZEN.read_text())
    study = json.loads(STUDY.read_text())
    source = json.loads(SOURCE.read_text())
    cases = {row["id"]: row for row in frozen["cases"]}
    base = source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
    record = {"status": "IN_PROGRESS", "frozen_sha256": frozen["sha256"],
              "study_sha256": digest(study), "source_proposal_sha256": digest(base),
              "execution": "scripted_user_answers_and_local_solver_runs; not live human interaction",
              "geometry_strategy": "fixed two-stage graph with bounded deterministic thickness sweep",
              "predeclared_thicknesses_mm": THICKNESSES_MM, "loops": []}
    for ident, answer in ANSWERS.items():
        original = cases[ident]["request"]
        model_row = study["results"][ident+"/muse_cold"]
        model = model_row["candidate"]
        assert model and model["decision"] == "clarify" and model["question_field"]
        merged = original + " " + answer
        specification = compile_intent(merged)
        assert specification["decision"] == "ready_for_static_beam_screen", ident
        c = specification["constraints"]
        assert c["drift_max_mm"] is not None and c["stress_max_mpa"] is not None
        material = MATERIALS[c["material"]]
        task = {"envelope_m": [v/1000 for v in c["envelope_mm"]],
                "material_properties": dict(material, depth_m=.01),
                "force_n": c["force_n"], "stroke_min_mm": c["stroke_min_mm"],
                "drift_max_mm": c["drift_max_mm"], "stress_max_mpa": c["stress_max_mpa"],
                "min_flexure_thickness_m": .0006}
        loop = {"id": ident, "original_request": original, "muse_question": model["question"],
                "muse_question_field": model["question_field"],
                "muse_receipt_index": model_row["receipt_index"],
                "scripted_answer": answer, "compiled_specification": specification,
                "solver_task": task,
                "declared_solver_assumptions": ["Nominal tabulated material E and yield, not batch certification",
                                                "Fixed 10 mm out-of-plane depth for this beam template"],
                "trials": [], "selected": None}
        for thickness in THICKNESSES_MM:
            candidate = copy.deepcopy(base)
            for edge in candidate["connections"]:
                edge["thickness"] = thickness/1000
            coarse = evaluate(candidate, task, mesh_density=16)
            trial = {"thickness_mm": thickness, "coarse": coarse, "fine": None}
            if coarse["feasible"]:
                fine = evaluate(candidate, task, mesh_density=48)
                trial["fine"] = fine
                if fine["feasible"] and loop["selected"] is None:
                    loop["selected"] = thickness
            loop["trials"].append(trial)
            print(ident, thickness, coarse["feasible"],
                  trial["fine"]["feasible"] if trial["fine"] else "not_run", flush=True)
            OUT.write_text(json.dumps(record | {"pending_loop": loop}, indent=2))
        loop["verdict"] = "fine_mesh_feasible" if loop["selected"] is not None else "unresolved_within_budget"
        record["loops"].append(loop)
        OUT.write_text(json.dumps(record, indent=2))
    record["status"] = "COMPLETE"
    OUT.write_text(json.dumps(record, indent=2))
    print("COMPLETE", [(x["id"], x["selected"], x["verdict"]) for x in record["loops"]])


if __name__ == "__main__":
    main()

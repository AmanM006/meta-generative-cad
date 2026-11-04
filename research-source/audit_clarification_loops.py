"""Recompute three scripted clarification conversations and every solver trial."""
import json
from pathlib import Path

from engineering_intent import compile_intent
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent


def main():
    record = json.loads((ROOT / "fresh_evidence/clarification_3_scripted_loops.json").read_text())
    study = json.loads((ROOT / "fresh_evidence/clarification_20_results.json").read_text())
    frozen = json.loads((ROOT / "fresh_evidence/clarification_20_frozen.json").read_text())
    source = json.loads((ROOT / "fresh_evidence/intent_spec_confirmatory_results.json").read_text())
    assert record["status"] == "COMPLETE" and len(record["loops"]) == 3
    assert record["frozen_sha256"] == frozen["sha256"]
    assert record["study_sha256"] == digest(study)
    base = source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
    assert record["source_proposal_sha256"] == digest(base)
    count = 0
    for loop in record["loops"]:
        ident = loop["id"]
        model_row = study["results"][ident+"/muse_cold"]
        assert loop["muse_receipt_index"] == model_row["receipt_index"]
        assert loop["muse_question"] == model_row["candidate"]["question"]
        assert loop["muse_question_field"] == model_row["candidate"]["question_field"]
        assert loop["compiled_specification"] == compile_intent(loop["original_request"]+" "+loop["scripted_answer"])
        assert [r["thickness_mm"] for r in loop["trials"]] == list(record["predeclared_thicknesses_mm"])
        first_pass = None
        for trial in loop["trials"]:
            candidate = trial["coarse"]["proposal"]
            assert candidate["anchors"] == base["anchors"] and candidate["stages"] == base["stages"]
            assert all(abs(edge["thickness"]-trial["thickness_mm"]/1000) < 1e-12 for edge in candidate["connections"])
            for kind, mesh in (("coarse", 16), ("fine", 48)):
                stored = trial[kind]
                if stored is None:
                    assert kind == "fine" and not trial["coarse"]["feasible"]
                    continue
                rerun = evaluate(candidate, loop["solver_task"], mesh_density=mesh)
                assert rerun["feasible"] == stored["feasible"] and rerun["gates"] == stored["gates"]
                for name in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                    assert abs(rerun[name]-stored[name]) < 1e-5
                count += 1
            if trial["fine"] and trial["fine"]["feasible"] and first_pass is None:
                first_pass = trial["thickness_mm"]
        assert loop["selected"] == first_pass
        assert loop["verdict"] == ("fine_mesh_feasible" if first_pass is not None else "unresolved_within_budget")
    result = {"status": "PASS", "loops": len(record["loops"]), "physics_recomputed": count,
              "selected_mm": {x["id"]: x["selected"] for x in record["loops"]}}
    (ROOT / "fresh_evidence/clarification_3_loops_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

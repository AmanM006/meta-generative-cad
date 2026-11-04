"""Check saved authenticated R10.1 production trace and selected physical gates."""
import json
from pathlib import Path

from audit_r9_matched import audit_solver_result, digest
from r101_action_space import apply_action
from run_r101_harness import metrics

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "fresh_evidence/r101_hosted_u02.json"


def main(path=EVIDENCE):
    data = json.loads(path.read_text())
    job = data["job"]
    assert data["source"] == "authenticated_hosted_public_api"
    assert data["repair_mode"] == "muse_adaptive"
    assert job["status"] == "completed"
    assert job["execution_mode"] == "LIVE_MUSE_ADAPTIVE_BEAM_FEA"
    assert job["selection_source"] == "muse_adaptive_proposal_independently_verified"
    assert "receipts" not in job and "job_token" not in json.dumps(data)
    assert len(job["provenance"]) == 3
    task = job["solver_task"]
    investigation = job["investigation"]
    baseline = investigation["baseline"]
    audit_solver_result(baseline["fine"],task)
    for corner in baseline["corners"]:
        audit_solver_result(corner["result"],corner["task"])
    current = baseline["fine"]["proposal"]
    candidate_count = 0
    verification_count = baseline["fea_evaluations"]
    for index, step in enumerate(investigation["steps"]):
        assert step["step"] == index+1
        assert step["candidate_sha256"] == digest(step["coarse"]["proposal"])
        assert step["coarse"]["proposal"] == apply_action(current,task,step["action"])
        audit_solver_result(step["coarse"],task)
        assert step["measured"] == metrics(step["coarse"],task)
        candidate_count += 1
        current = step["coarse"]["proposal"]
        if step.get("verification"):
            check = step["verification"]
            audit_solver_result(check["fine"],task)
            for corner in check["corners"]:
                audit_solver_result(corner["result"],corner["task"])
            assert check["robust"] == bool(check["fine"]["feasible"] and len(check["corners"])==4
                                           and all(x["result"]["feasible"] for x in check["corners"]))
            verification_count += check["fea_evaluations"]
    assert investigation["candidate_fea_evaluations"] == candidate_count
    assert investigation["verification_fea_evaluations"] == verification_count
    assert investigation["steps"][-1]["verification"]["robust"]
    assert job["selected_proposal"] == current
    assert len(job["selected_proposal"]["connections"]) == 6
    return {"status":job["status"],"adaptive_steps":len(investigation["steps"]),
            "model_receipts":len(job["provenance"]),"candidate_fea":candidate_count,
            "verification_fea":verification_count,"selected_geometry_sha256":digest(current)}


if __name__ == "__main__":
    print(main())

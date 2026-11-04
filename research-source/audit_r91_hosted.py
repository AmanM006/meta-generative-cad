"""Independent numerical checks of the redacted hosted R9 episode."""
import json
from pathlib import Path

from audit_r9_matched import audit_solver_result, digest

ROOT = Path(__file__).resolve().parent
PATH = ROOT / "fresh_evidence/r91_hosted_c01.json"


def main():
    evidence = json.loads(PATH.read_text())
    assert evidence["source"] == "authenticated_hosted_public_api"
    job = evidence["job"]
    assert job["status"] == "completed"
    assert job["verdict"] == "joint_corner_beam_pass"
    assert len(job["provenance"]) == 2
    assert all(r["request_id"] and r["request_sha256"] and r["response_sha256"] for r in job["provenance"])
    assert job["evaluated_geometry_sha256"] and job["selected_proposal"]
    assert "job_token" not in job and "access_code" not in job and "receipts" not in job
    task = job["solver_task"]
    evaluations = 0
    for trial in job["trials"]:
        for result in (trial["coarse"], trial["fine"]):
            if result:
                audit_solver_result(result, task)
                evaluations += 1
        for corner in trial["joint_corners"]:
            audit_solver_result(corner["result"], task)
            evaluations += 1
    repair = job["repair_attempt"]
    assert repair["verdict"] == "robust_beam_pass"
    assert repair["candidate_sha256"] == digest(repair["candidate"]["proposal"])
    for result in (repair["candidate"]["coarse"], repair["candidate"]["fine"],
                   repair["measured_failed_scenario_after"]):
        audit_solver_result(result, task)
        evaluations += 1
    for corner in repair["candidate"]["joint_corners"]:
        audit_solver_result(corner["result"], task)
        evaluations += 1
    assert all(x["result"]["feasible"] for x in repair["candidate"]["joint_corners"])
    assert digest(job["selected_proposal"]) == repair["candidate_sha256"]
    print({"hosted_status": job["status"], "meta_receipts": len(job["provenance"]),
           "repair_action": repair["hypothesis"]["action"],
           "repair_verdict": repair["verdict"], "audited_evaluations": evaluations,
           "selected_geometry_hash": repair["candidate_sha256"]})


if __name__ == "__main__":
    main()

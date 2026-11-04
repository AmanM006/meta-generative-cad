"""Audit immutable fields in the one-call C01 local live run without API spend."""
import hashlib
import json
from pathlib import Path

from open_ended_structural_discovery_engine import digest

EVIDENCE = Path(__file__).parent / "fresh_evidence/live_c01_local_2026_11_04.json"
HOSTED = Path(__file__).parent / "fresh_evidence/live_c01_hosted_2026_11_04.json"


def main():
    job = json.loads(EVIDENCE.read_text())
    assert job["execution_mode"] == "LIVE_MUSE_LIVE_BEAM_FEA"
    assert job["status"] == "completed"
    assert len(job["receipts"]) == 1
    receipt = job["receipts"][0]
    assert digest(receipt["request"]) == receipt["request_sha256"]
    assert hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"]
    assert receipt["prompt_tokens"] == 398 and receipt["completion_tokens"] == 525
    assert abs(receipt["estimated_cost_usd"] - .0004996) < 1e-10
    assert receipt["actual_billed_cost_usd"] == "UNKNOWN"
    assert len(job["trials"]) == 5
    assert [t["thickness_mm"] for t in job["trials"]] == [.6, .7, .8, .9, 1.0]
    assert job["trials"][3]["coarse"]["feasible"]
    assert job["trials"][3]["fine"]["feasible"]
    assert [c["result"]["feasible"] for c in job["trials"][3]["joint_corners"]] == [False, True, True, True]
    assert all(c["result"]["feasible"] for c in job["trials"][4]["joint_corners"])
    assert job["selected_mm"] == 1.0 and job["verdict"] == "joint_corner_beam_pass"
    print("PASS: one Meta receipt hashes, 923 tokens, $0.0004996 estimated; five live FEA trials; 0.9 mm fails one corner, 1.0 mm passes four")
    hosted = json.loads(HOSTED.read_text())
    assert hosted["execution_mode"] == "LIVE_MUSE_LIVE_BEAM_FEA"
    assert hosted["status"] == "completed" and hosted["error"] is None
    assert hosted["solver_task"] == job["solver_task"]
    assert hosted["geometry_source_sha256"] == job["geometry_source_sha256"]
    assert len(hosted["provenance"]) == 1 and hosted["provenance"][0]["request_id"].startswith("chatcmpl-")
    assert abs(hosted["provenance"][0]["estimated_cost_usd"] - .0004564) < 1e-10
    assert len(hosted["trials"]) == 5
    for local_trial, hosted_trial in zip(job["trials"], hosted["trials"]):
        assert local_trial["thickness_mm"] == hosted_trial["thickness_mm"]
        assert local_trial["coarse"]["feasible"] == hosted_trial["coarse"]["feasible"]
        assert abs(local_trial["coarse"]["stroke_mm"] - hosted_trial["coarse"]["stroke_mm"]) < 1e-8
    assert [c["result"]["feasible"] for c in hosted["trials"][3]["joint_corners"]] == [False, True, True, True]
    assert all(c["result"]["feasible"] for c in hosted["trials"][4]["joint_corners"])
    assert hosted["selected_mm"] == 1.0 and hosted["verdict"] == "joint_corner_beam_pass"
    print("PASS: hosted Meta receipt provenance, $0.0004564 estimated; identical task and FEA results; 1.0 mm robust beam-model selection")


if __name__ == "__main__":
    main()

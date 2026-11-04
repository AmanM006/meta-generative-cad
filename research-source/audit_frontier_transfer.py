"""Audit frozen transfer receipts and optionally recompute every physical result.

Usage: python audit_frontier_transfer.py [--physics]
The fast mode verifies hashes and independent conclusion arithmetic. Physics
mode reruns all stored FEA proposals, including the corrected classical arm.
"""
import argparse
import hashlib
import json
from pathlib import Path

from frontier_transfer_study import classical_candidates
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "fresh_evidence/frontier_transfer_tasks_frozen.json"
LEDGER = ROOT / "fresh_evidence/frontier_transfer_study.json"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def audit(physics=False):
    frozen = json.loads(TASKS.read_text())
    study = json.loads(LEDGER.read_text())
    prior = json.loads((ROOT / "fresh_evidence/frontier_novel_graph_challenge.json").read_text())
    body = {k: v for k, v in frozen.items() if k != "frozen_spec_sha256"}
    check(digest(body) == frozen["frozen_spec_sha256"], "frozen task checksum")
    check(study["frozen_spec_sha256"] == frozen["frozen_spec_sha256"], "ledger task binding")
    check(study["source_prior_sha256"] == digest(prior), "discovery source binding")
    for i, receipt in enumerate(study["receipts"]):
        check(digest(receipt["request"]) == receipt["request_sha256"], f"request hash {i}")
        check(hashlib.sha256(receipt["response"].encode()).hexdigest() == receipt["response_sha256"],
              f"response hash {i}")
        check(receipt["cost_usd"] >= 0, f"cost {i}")
    check(abs(sum(r["cost_usd"] for r in study["receipts"]) - study["new_model_cost_usd"]) < 1e-10,
          "model cost sum")
    discovery = study["discovery"]
    before = discovery["independent_adjudication"]["measured_before_stroke_mm"]
    after = discovery["experiment_result"]["stroke_mm"]
    check(after < before and discovery["independent_adjudication"]["hypothesis_supported"] is False,
          "failed hypothesis must remain rejected")
    counts = {}
    evaluated = 0
    for task in frozen["tasks"]:
        for arm in frozen["arms"]:
            key = task["id"] + "/" + arm
            row = study["transfer"][key]
            coarse = row["corrected_coarse"] if arm == "deterministic_physics" else row["coarse"]
            fine = row["corrected_fine_best"] if arm == "deterministic_physics" else row["fine_best"]
            check(len(coarse) == frozen["max_fea_per_task_per_arm"], f"trial budget {key}")
            if arm != "deterministic_physics":
                receipt = study["receipts"][row["receipt_index"]]
                parsed = json.loads(receipt["response"].strip().removeprefix("```json").removesuffix("```").strip())
                proposals = parsed.get("proposals", [])[:2]
                for stored, proposal in zip(coarse, proposals):
                    check(stored.get("proposal_sha256", digest(stored.get("proposal"))) == digest(proposal),
                          f"model response proposal binding {key}")
            if arm == "deterministic_physics":
                check([digest(p) for p in classical_candidates(task)] ==
                      [r["proposal_sha256"] for r in coarse], f"classical proposal replay {key}")
            if physics:
                for stored in coarse + ([fine] if fine.get("status") == "evaluated" else []):
                    if stored.get("status") != "evaluated":
                        continue
                    result = evaluate(stored["proposal"], task, stored["mesh_elements_per_beam"])
                    check(result["status"] == stored["status"], f"status replay {key}")
                    check(result["feasible"] == stored["feasible"], f"feasibility replay {key}")
                    for field in ("stroke_mm", "absolute_drift_mm", "stress_mpa"):
                        check(abs(result[field]-stored[field]) < 1e-5, f"{field} replay {key}")
                    evaluated += 1
            counts.setdefault(arm, {"fine_feasible_tasks": 0, "coarse_feasible_proposals": 0,
                                    "invalid_or_missing_proposals": 0})
            counts[arm]["fine_feasible_tasks"] += int(fine["feasible"])
            counts[arm]["coarse_feasible_proposals"] += sum(bool(r.get("feasible")) for r in coarse)
            counts[arm]["invalid_or_missing_proposals"] += sum(r.get("status") != "evaluated" for r in coarse)
    check(counts["deterministic_physics"]["fine_feasible_tasks"] == 2, "baseline verdict")
    check(counts["muse_raw_history"]["fine_feasible_tasks"] == 1, "raw history verdict")
    check(counts["muse_validated_principle"]["fine_feasible_tasks"] == 1, "principle prompt verdict")
    return {"status": "PASS", "frozen_spec_sha256": frozen["frozen_spec_sha256"],
            "receipts_verified": len(study["receipts"]), "new_model_cost_usd": study["new_model_cost_usd"],
            "physics_results_recomputed": evaluated, "counts": counts,
            "principle_status": "REJECTED_BY_DISCOVERY_EXPERIMENT"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--physics", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.physics), indent=2))

"""Resumable, bounded paired R9 experiment on the previously frozen task set."""
import argparse
import asyncio
import hashlib
import json
import os
import secrets
import time
from pathlib import Path

import live_engineering_service as live
from engineering_intent import compile_intent
from fresh_matched_benchmark import meta_key
from r9_repair_policy import mutate

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/r9_frozen_tasks.json"
PROTOCOL = ROOT / "fresh_evidence/r9_matched_protocol.json"
BASELINE = ROOT / "fresh_evidence/r9_generalization_results.json"
MODES = {"B": "deterministic", "C": "muse_directed", "D": "muse_casm_repair"}


def audited_inputs():
    frozen_bytes = FROZEN.read_bytes()
    protocol = json.loads(PROTOCOL.read_text())
    frozen_hash = hashlib.sha256(frozen_bytes).hexdigest()
    assert protocol["task_set_sha256"] == frozen_hash
    return json.loads(frozen_bytes), protocol, frozen_hash


def save(output, data):
    output.write_text(json.dumps(data, indent=2))


def summarize(job, case):
    reference = case.get("constraints", case.get("constraints_after_answer"))
    actual = (job.get("specification") or {}).get("constraints") or {}
    receipts = job.get("receipts", [])
    repair = job.get("repair_attempt") or {}
    return {
        "status": job["status"], "error": job.get("error"),
        "correct_fields": sum(actual.get(k) == value for k, value in reference.items()),
        "all_six_fields_correct": actual == reference,
        "clarification_field": next((e["detail"].get("field") for e in job["events"]
                                     if e["step"] == "clarification_question"), None),
        "repair_verdict": repair.get("verdict"),
        "repair_action": (repair.get("hypothesis") or {}).get("action"),
        "prediction_both_correct": (repair.get("prediction_check") or {}).get("both_correct"),
        "robust_before_fallback": repair.get("verdict") == "robust_beam_pass",
        "final_robust": job.get("verdict") == "joint_corner_beam_pass",
        "selection_source": job.get("selection_source"),
        "selected_design": job.get("selected_design"),
        "trial_count": len(job.get("trials", [])),
        "model_calls_with_receipts": len(receipts),
        "prompt_tokens": sum(r["prompt_tokens"] for r in receipts),
        "completion_tokens": sum(r["completion_tokens"] for r in receipts),
        "estimated_cost_usd": sum(r["estimated_cost_usd"] for r in receipts),
    }


async def model_arm(arm, cases, frozen_hash):
    key = meta_key()
    if not key:
        raise RuntimeError("Local Meta credential unavailable")
    os.environ["MODEL_API_KEY"] = key
    code = secrets.token_urlsafe(24)
    os.environ["LIVE_DEMO_ACCESS_CODE"] = code
    live.BUDGET_FILE = live.PRIVATE / "r9_benchmark_budget.json"
    live.MAX_MODEL_CALLS = 32  # Local bounded campaign; hosted service remains at 16.
    live.MAX_MODEL_ESTIMATED_USD = .05
    output = ROOT / f"fresh_evidence/r9_arm_{arm}.json"
    data = json.loads(output.read_text()) if output.exists() else {
        "arm": arm, "frozen_sha256": frozen_hash,
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "local_model_ceiling": {"calls": 32, "estimated_usd": .05}, "cases": {}}
    for case in cases:
        ident = case["id"]
        if ident in data["cases"]:
            previous = data["cases"][ident]
            if (previous["summary"]["status"] == "error"
                    and "APIConnectionError" in str(previous["summary"].get("error"))
                    and previous["summary"]["model_calls_with_receipts"] == 0):
                data.setdefault("connection_retries", {}).setdefault(ident, []).append(previous)
                del data["cases"][ident]
                save(output, data)
            else:
                print(arm, ident, "already_saved", flush=True)
                continue
        started_at = time.perf_counter()
        started = await live.start(live.StartRequest(
            request_text=case["request"], access_code=code, repair_mode=MODES[arm]))
        token = started["job_token"]
        job = live.JOBS[started["id"]]
        answered = False
        for _ in range(1200):
            if job["status"] == "needs_clarification":
                field = job["question"]["field"]
                if case.get("answer") and field == "force_n" and not answered:
                    await live.answer(job["id"], live.AnswerRequest(
                        access_code=code, job_token=token, answer=case["answer"]))
                    answered = True
                else:
                    job["status"] = "protocol_question_error"
                    live.event(job, "benchmark_protocol_question_error", {"field": field})
            if job["status"] in {"completed", "unresolved", "error", "abstained",
                                  "needs_manual_revision", "protocol_question_error"}:
                break
            await asyncio.sleep(.5)
        else:
            job["status"] = "benchmark_timeout"
            live.event(job, "benchmark_timeout", "600 s case limit")
        data["cases"][ident] = {"summary": summarize(job, case),
                                "duration_s": time.perf_counter() - started_at,
                                "raw_job": job}
        save(output, data)
        print(arm, ident, job["status"], job.get("selection_source"),
              len(job.get("receipts", [])), round(data["cases"][ident]["duration_s"], 1), flush=True)
    print("budget", {"reserved_calls": live.budget()["reserved_calls"],
                     "estimated_spend_usd": live.budget()["estimated_spend_usd"]}, flush=True)


async def deterministic_menu(cases, frozen_hash):
    baseline = json.loads(BASELINE.read_text())["cases"]
    output = ROOT / "fresh_evidence/r9_arm_E.json"
    data = json.loads(output.read_text()) if output.exists() else {
        "arm": "E", "frozen_sha256": frozen_hash,
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "model_calls": 0, "cases": {}}
    for case in cases:
        ident = case["id"]
        if ident in data["cases"]:
            continue
        source = baseline[ident]
        first = next(t for t in source["trials"] if t["fine"] is not None and t["fine"]["feasible"]
                     and any(not x["result"]["feasible"] for x in t["joint_corners"]))
        failed = next(x for x in first["joint_corners"] if not x["result"]["feasible"])
        action = ("outer_plus_0p1" if "absolute_drift" in
                  [k for k, okay in failed["result"].get("gates", {}).items() if not okay]
                  else "uniform_plus_0p1")
        start = time.perf_counter()
        candidate = mutate(first["fine"]["proposal"], action)
        measured = await live.measure_repair_action(candidate, source["solver_task"], failed)
        data["cases"][ident] = {
            "request": case["request"], "action": action,
            "initial_uniform_selected_mm": source["selected_mm"],
            "repair_verdict": measured["verdict"],
            "robust_before_fallback": measured["verdict"] == "robust_beam_pass",
            "final_robust": measured["verdict"] == "robust_beam_pass" or source["selected_mm"] is not None,
            "duration_s": time.perf_counter() - start,
            "measured": measured,
        }
        save(output, data)
        print("E", ident, action, measured["verdict"], round(data["cases"][ident]["duration_s"], 1), flush=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=["B", "C", "D", "E"])
    args = parser.parse_args()
    frozen, protocol, frozen_hash = audited_inputs()
    cases = [next(c for c in frozen["cases"] if c["id"] == ident) for ident in protocol["cases"]]
    if args.arm == "E":
        await deterministic_menu(cases, frozen_hash)
    else:
        await model_arm(args.arm, cases, frozen_hash)


if __name__ == "__main__":
    asyncio.run(main())

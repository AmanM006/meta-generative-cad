"""Resumable, budgeted R9.1 paired one-step repair experiment."""
import argparse
import asyncio
import hashlib
import json
import os
import time
from pathlib import Path

import live_engineering_service as live
from fresh_matched_benchmark import meta_key
from r9_repair_policy import failure_metrics, mutate, parse_repair, repair_prompt

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "fresh_evidence"
TASKS = EVIDENCE / "r91_frozen_tasks.json"
PROTOCOL = EVIDENCE / "r91_frozen_protocol.json"
BASELINES = EVIDENCE / "r91_baselines.json"
HISTORY = EVIDENCE / "r9_arm_E.json"
HISTORY_D = EVIDENCE / "r9_arm_D.json"


def read_inputs():
    protocol = json.loads(PROTOCOL.read_text())
    task_hash = hashlib.sha256(TASKS.read_bytes()).hexdigest()
    protocol_hash = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    assert protocol["task_set_sha256"] == task_hash
    baseline = json.loads(BASELINES.read_text())
    assert baseline["task_sha256"] == task_hash and baseline["protocol_sha256"] == protocol_hash
    return json.loads(TASKS.read_text())["cases"], baseline["cases"], task_hash, protocol_hash


def historical_records(material):
    frozen = json.loads((EVIDENCE / "r9_frozen_tasks.json").read_text())["cases"]
    cases = {x["id"]: x for x in frozen}
    rule = json.loads(HISTORY.read_text())["cases"]
    casm = json.loads(HISTORY_D.read_text())["cases"]
    ids = (["G01_low_force_precision", "G02_moderate_guidance"] if material == "polypropylene"
           else ["G04_petg_material"])
    records = []
    def physical_values(result):
        return {key: result.get(key) for key in ("stroke_mm", "absolute_drift_mm", "stress_mpa", "feasible", "gates")}
    for ident in ids:
        actions = [{"action": rule[ident]["action"], "verdict": rule[ident]["repair_verdict"],
                    "result": physical_values(rule[ident]["measured"]["measured_failed_scenario_after"])}]
        if casm[ident]["summary"]["repair_action"] != actions[0]["action"]:
            repair = casm[ident]["raw_job"]["repair_attempt"]
            actions.append({"action": casm[ident]["summary"]["repair_action"],
                            "verdict": repair["verdict"],
                            "result": physical_values(repair["measured_failed_scenario_after"])})
        records.append({"id": ident, "constraints": cases[ident]["constraints_after_answer"]
                        if "constraints_after_answer" in cases[ident] else cases[ident]["constraints"],
                        "experiments": actions})
    return records


def memory_context(material, arm, control=None):
    records = historical_records(material)
    if control == "irrelevant_memory":
        records = historical_records("petg" if material == "polypropylene" else "polypropylene")
    if arm == "C" or control == "irrelevant_memory":
        return {"kind": "raw_prior_experiments", "retrieval": "material match then frozen R9 ID order" if not control else "deliberately irrelevant material",
                "records": records, "warning": "Historical tasks only; no current task outcome"}
    if arm == "D" or control == "contradictory_memory":
        if control == "contradictory_memory":
            return {"kind": "synthetic_contradictory_negative_control",
                    "principle": "Outer-beam thickening always passes while uniform thickening always fails.",
                    "counterexample": "This reverses the stored PETG G04 outcomes and is intentionally false."}
        if material == "petg":
            return {"kind": "single_precedent_distilled_memory", "principle_id": "R9-G04-PETG-UNIFORM",
                    "applicability": "PETG material match; different envelope, force and stroke still require new FEA",
                    "principle": "In one measured PETG case, uniform +0.1 mm passed all corners.",
                    "counterexample_id": "R9-G04-PETG-OUTER-FAIL",
                    "counterexample": "Outer-only +0.1 mm failed the R9 G04 joint check.",
                    "same_underlying_records": records,
                    "warning": "One-case precedent, not a general mechanical law or current-case result"}
        return {"kind": "small_measured_distilled_memory", "principle_id": "R9-PP-THICKNESS",
                "applicability": "PP material match; different envelope, force and stroke require new FEA",
                "principle": "Uniform +0.1 mm passed one prior PP manufacturing-floor case; outer +0.1 mm passed one prior PP drift case.",
                "counterexample_id": "R9-G04-PETG-OUTER-FAIL",
                "counterexample": "Outer-only +0.1 mm failed in a different PETG task; do not generalize across materials.",
                "same_underlying_records": records,
                "warning": "Small historical sample, not current-case validation"}
    return None


def prompt_for(case, baseline, arm, control=None):
    failure = failure_metrics(baseline["failed"]["result"], baseline["failed"]["task"])
    base = repair_prompt(baseline["specification"], failure, case["baseline_uniform_thickness_mm"])
    base = base.replace("Use only the observed failure and allowed experiments below.",
                        "Use the observed failure, allowed experiments, and any labeled historical context below.")
    context = memory_context(case["constraints"]["material"], arm, control)
    if context:
        base += "\nHISTORICAL_CONTEXT_JSON: " + json.dumps(context, sort_keys=True)
    return base, failure, context


def save(path, value):
    path.write_text(json.dumps(value, indent=2))


async def run_arm(arm, cases, baselines, task_hash, protocol_hash, controls=False):
    output = EVIDENCE / (f"r91_arm_{arm}.json" if not controls else "r91_negative_controls.json")
    data = json.loads(output.read_text()) if output.exists() else {
        "arm": arm, "task_sha256": task_hash, "protocol_sha256": protocol_hash, "cases": {}}
    assert data["task_sha256"] == task_hash and data["protocol_sha256"] == protocol_hash
    if arm in "BCD" or controls:
        key = meta_key()
        if not key:
            raise RuntimeError("Local Meta credential unavailable")
        os.environ["MODEL_API_KEY"] = key
        live.BUDGET_FILE = live.PRIVATE / "r91_model_budget.json"
        live.MAX_MODEL_CALLS = 48
        live.MAX_MODEL_ESTIMATED_USD = .05
    for case in cases:
        ident = case["id"]
        if controls and ident not in {"T03", "T08"}:
            continue
        variants = (["irrelevant_memory", "contradictory_memory"] if controls else [None])
        for control in variants:
            key = ident if control is None else ident + "/" + control
            if key in data["cases"]:
                continue
            baseline = baselines[ident]
            started = time.perf_counter()
            if baseline["status"] != "repair_needed":
                record = {"status": baseline["status"], "one_step_robust": baseline["status"] == "already_robust",
                          "action": None, "model_receipt": None, "fea_evaluations": 0}
            elif arm == "E" and not controls:
                attempts = []
                for action in ("uniform_plus_0p1", "outer_plus_0p1", "bridge_plus_0p1"):
                    candidate = mutate(baseline["baseline_proposal"], action)
                    measured = await live.measure_repair_action(candidate, baseline["solver_task"], baseline["failed"])
                    attempts.append({"action": action, "measured": measured})
                selected = next((x for x in attempts if x["measured"]["verdict"] == "robust_beam_pass"), None)
                record = {"status": "evaluated", "one_step_robust": bool(selected),
                          "action": selected["action"] if selected else None, "attempts": attempts,
                          "model_receipt": None, "fea_evaluations": sum(2 + (1 if x["measured"]["candidate"]["fine"] else 0)
                          + max(0, len(x["measured"]["candidate"]["joint_corners"]) - 1)
                          for x in attempts)}
            elif arm == "A" and not controls:
                failure = failure_metrics(baseline["failed"]["result"], baseline["failed"]["task"])
                action = "outer_plus_0p1" if "absolute_drift" in failure["failed_gates"] else "uniform_plus_0p1"
                measured = await live.measure_repair_action(mutate(baseline["baseline_proposal"], action),
                                                             baseline["solver_task"], baseline["failed"])
                record = {"status": "evaluated", "one_step_robust": measured["verdict"] == "robust_beam_pass",
                          "action": action, "failure": failure, "measured": measured,
                          "model_receipt": None, "fea_evaluations": 2 + (1 if measured["candidate"]["fine"] else 0)
                          + max(0, len(measured["candidate"]["joint_corners"]) - 1)}
            else:
                actual_arm = "D" if controls else arm
                prompt, failure, context = prompt_for(case, baseline, actual_arm, control)
                record = {"status": "model_pending", "failure": failure,
                          "historical_context": context, "model_prompt": prompt,
                          "model_raw": None, "model_receipt": None,
                          "one_step_robust": False, "action": None, "fea_evaluations": 0}
                try:
                    await live.reserve_model_call()
                    raw, receipt = await asyncio.wait_for(asyncio.to_thread(live.call_muse_repair_live, prompt), timeout=70)
                    record["model_raw"] = raw
                    record["model_receipt"] = receipt
                    await live.settle_model_call(receipt)
                    choice = parse_repair(raw, failure["failed_gates"])
                    record["choice"] = choice
                    record["action"] = choice["action"]
                    candidate = mutate(baseline["baseline_proposal"], choice["action"])
                    measured = await live.measure_repair_action(candidate, baseline["solver_task"], baseline["failed"])
                    record["measured"] = measured
                    record["one_step_robust"] = measured["verdict"] == "robust_beam_pass"
                    record["prediction_both_correct"] = (
                        (choice["predicted_stroke_direction"] == measured["measured_directions"]["stroke"]
                         and choice["predicted_drift_direction"] == measured["measured_directions"]["drift"])
                        if measured["measured_directions"]["stroke"] != "unscorable" else None)
                    record["fea_evaluations"] = (2 + (1 if measured["candidate"]["fine"] else 0)
                        + max(0, len(measured["candidate"]["joint_corners"]) - 1))
                    record["status"] = "evaluated"
                except Exception as exc:
                    record["status"] = "invalid_or_failed_" + type(exc).__name__
                    record["error_type"] = type(exc).__name__
            record["duration_s"] = time.perf_counter() - started
            data["cases"][key] = record
            save(output, data)
            print(arm if not controls else "N", key, record["status"], record["action"],
                  record["one_step_robust"], flush=True)
    if arm in "BCD" or controls:
        print("budget", live.budget(), flush=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["A", "B", "C", "D", "E", "N"], required=True)
    args = parser.parse_args()
    cases, baselines, task_hash, protocol_hash = read_inputs()
    await run_arm("D" if args.arm == "N" else args.arm, cases, baselines, task_hash,
                  protocol_hash, controls=args.arm == "N")


if __name__ == "__main__":
    asyncio.run(main())

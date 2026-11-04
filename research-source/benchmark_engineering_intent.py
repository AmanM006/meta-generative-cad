"""Frozen, receipt-backed natural-language specification benchmark."""
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from engineering_intent import MATERIALS, compile_intent, validate_model_interpretation
from fresh_matched_benchmark import meta_key
from frontier_transfer_study import classical_candidates
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "fresh_evidence/intent_spec_benchmark_frozen.json"
OUT = ROOT / "fresh_evidence/intent_spec_benchmark_results.json"
MAX_PILOT_COST_USD = 0.10


def save(state):
    OUT.write_text(json.dumps(state, indent=2))


def call_muse(prompt, state):
    key = meta_key()
    if not key:
        raise RuntimeError("MODEL_API_KEY unavailable")
    if sum(r["cost_usd"] for r in state["receipts"]) >= MAX_PILOT_COST_USD - 0.01:
        raise RuntimeError("Pilot API budget reached")
    request = {"model": "muse-spark-1.3", "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.0, "reasoning_effort": "minimal", "max_completion_tokens": 1100}
    started = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=key, timeout=60).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    receipt = {"request_id": response.id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "request": request, "request_sha256": digest(request), "response": raw,
               "response_sha256": hashlib.sha256(raw.encode()).hexdigest(), "model": response.model,
               "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
               "cost_usd": (usage.prompt_tokens*.20+usage.completion_tokens*.80)/1e6,
               "latency_s": time.perf_counter()-started, "finish_reason": response.choices[0].finish_reason}
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    except ValueError:
        parsed = None
    return parsed, receipt


def prompt_for(case, memory=False):
    prompt = (
        "Interpret this engineering request for a 2D static nonlinear beam-screening tool. "
        "Do not invent absent values. Return ONLY JSON with decision one of "
        "ready_for_static_beam_screen, needs_clarification, contradictory, unsupported_physics; "
        "constraints object with EXACT keys material, force_n, stroke_min_mm, envelope_mm, "
        "drift_max_mm, stress_max_mpa. Unknown values must be null. "
        "Use N, mm, MPa; convert mN and micrometers. "
        "Known materials: polypropylene (PP), PETG, aluminum. "
        "A ready specification requires material, force, stroke and envelope; drift and stress are optional. "
        "Treat snap-through, bistability, fatigue, thermal cycling, vibration, impact and buckling-load certification "
        "as unsupported; zero force with positive actuation stroke, stroke at least package height, and stress "
        "limits above listed yield strength as contradictions. Yield strengths: PP 35 MPa, PETG 45 MPa, "
        "aluminum 240 MPa. Request: " + case["request"]
    )
    if memory:
        prompt += ("\nScientific memory counterexample: In a prior two-stage PP mechanism, Muse predicted that "
                   "increasing stage height would improve stroke; FEA measured a decrease from 1.9867 to "
                   "1.6837 mm. Treat mechanistic rules as provisional. Do not fill missing task requirements "
                   "from remembered examples or certify an unsupported capability.")
    return prompt


def score(candidate, reference):
    if candidate is None:
        return {"decision_correct": False, "fields_correct": 0, "complete_correct": False}
    keys = reference["constraints"]
    correct = 0
    for key, expected in keys.items():
        actual = candidate["constraints"].get(key)
        if isinstance(expected, list):
            match = isinstance(actual, list) and len(actual) == len(expected) and all(
                isinstance(v, (float, int)) and abs(v-e) < 1e-6 for v, e in zip(actual, expected))
        elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
            match = isinstance(actual, (float, int)) and abs(actual-expected) < 1e-6
        else:
            match = actual == expected
        correct += int(match)
    decision_correct = candidate["decision"] == reference["decision"]
    return {"decision_correct": decision_correct, "fields_correct": correct,
            "complete_correct": decision_correct and correct == len(keys)}


def screen(candidate, raw_text):
    if candidate is None or candidate["decision"] != "ready_for_static_beam_screen":
        return {"status": "not_screened", "reason": "Specification incomplete, contradictory, or unsupported"}
    safety = compile_intent(raw_text)
    if safety["decision"] in {"contradictory", "unsupported_physics"}:
        return {"status": "blocked_by_independent_safety_gate", "reason": safety["decision"]}
    c = candidate["constraints"]
    task = {"envelope_m": [v/1000 for v in c["envelope_mm"]],
            "material_properties": dict(MATERIALS[c["material"]], depth_m=.01),
            "force_n": c["force_n"], "stroke_min_mm": c["stroke_min_mm"],
            "drift_max_mm": c["drift_max_mm"] if c["drift_max_mm"] is not None else .06,
            "stress_max_mpa": c["stress_max_mpa"] if c["stress_max_mpa"] is not None else MATERIALS[c["material"]]["yield_strength_pa"]/1e6,
            "min_flexure_thickness_m": .0006}
    proposal = classical_candidates(task)[0]
    result = evaluate(proposal, task)
    return {"status": "screened", "task": task, "physics": result,
            "certification": "beam_model_screen_only" if result.get("feasible") else "failed_or_rejected"}


def main():
    frozen = json.loads(SPEC.read_text())
    check = {k: v for k, v in frozen.items() if k != "sha256"}
    if digest(check) != frozen["sha256"]:
        raise RuntimeError("Frozen benchmark checksum mismatch")
    state = json.loads(OUT.read_text()) if OUT.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(), "frozen_sha256": frozen["sha256"],
        "arms": frozen["model_arms"], "results": {}, "receipts": []}
    if state["frozen_sha256"] != frozen["sha256"]:
        raise RuntimeError("Existing results bind to another benchmark")
    for case in frozen["held_out"]:
        for arm in frozen["model_arms"]:
            key = case["id"] + "/" + arm
            if key in state["results"]:
                continue
            if arm == "deterministic":
                candidate, receipt_index, failure = compile_intent(case["request"]), None, None
            else:
                parsed, receipt = call_muse(prompt_for(case, arm == "muse_with_counterexample_memory"), state)
                receipt_index = len(state["receipts"])
                state["receipts"].append(receipt)
                save(state)
                try:
                    candidate = validate_model_interpretation(case["request"], parsed)
                    failure = None
                except (ValueError, TypeError) as exc:
                    candidate, failure = None, str(exc)
            metrics = score(candidate, case["reference"])
            physical = screen(candidate, case["request"])
            state["results"][key] = {"candidate": candidate, "receipt_index": receipt_index,
                                      "parse_or_validation_failure": failure, "score": metrics,
                                      "physical_screen": physical}
            save(state)
            print(key,metrics,"screen",physical["status"],flush=True)
    state["status"] = "COMPLETE"
    state["new_cost_usd"] = sum(r["cost_usd"] for r in state["receipts"])
    save(state)
    print("COMPLETE",state["new_cost_usd"])


if __name__ == "__main__":
    main()

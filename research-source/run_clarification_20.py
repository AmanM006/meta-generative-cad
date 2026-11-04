"""Matched clarification benchmark with raw, resumable Meta Muse receipts."""
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from engineering_intent_clarification_baseline import compile_intent, clarification
from fresh_matched_benchmark import meta_key
from open_ended_structural_discovery_engine import digest

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/clarification_20_frozen.json"
LEDGER = ROOT / "fresh_evidence/clarification_20_results.json"
MODEL = "muse-spark-1.3"
ARM_ORDER = ("deterministic", "muse_cold", "muse_raw_memory", "muse_validated_memory")
FIELDS = ("material", "force_n", "stroke_min_mm", "envelope_mm", "drift_max_mm", "stress_max_mpa")
REQUIRED = ("material", "force_n", "stroke_min_mm", "envelope_mm")
QUESTION_FIELDS = (*REQUIRED, "material_properties")
ISSUES = ("conflicting_stroke", "conflicting_drift", "ambiguous_material",
          "unsupported_manufacturing", "out_of_plane_loading", "uncertain_modulus",
          "zero_force_positive_stroke", "package_below_scale", "fatigue", "stress_above_yield")
MAX_NEW_ESTIMATED_USD = 0.15

RAW_MEMORY = ("Unfiltered historical observations: increasing a stage height once reduced stroke "
              "from 1.9867 to 1.6837 mm; a 0.9 mm PP flexure passed nominally; one earlier "
              "open-graph trial was feasible; a 3D replay reached 3.007 mm stroke. These "
              "observations came from different tasks and are not universal rules.")
VALIDATED_MEMORY = ("Validated scope and counterexamples: a previous 0.9 mm PP design passed "
                    "nominal beam FEA but failed combined low-thickness/low-modulus drift. "
                    "The 2D static beam solver cannot certify fatigue or out-of-plane loads. "
                    "Do not infer missing force, package, material properties or safety limits "
                    "from prior designs. Use memory only if relevant to the present request.")


def save(state):
    LEDGER.write_text(json.dumps(state, indent=2))


def prompt_for(request, arm):
    prompt = (
        "You are compiling a user's engineering request for a 2D static nonlinear beam screen. "
        "Return ONLY one JSON object with EXACT top-level keys decision, constraints, missing, "
        "question_field, question, issue_codes. decision must be proceed, clarify, or abstain. "
        "constraints must contain EXACT keys material, force_n, stroke_min_mm, envelope_mm, "
        "drift_max_mm, stress_max_mpa. Unknown values must be null. Use canonical materials "
        "polypropylene, petg, aluminum. Convert mN to N and micrometers to mm. "
        "missing lists only absent required keys among material, force_n, stroke_min_mm, envelope_mm. "
        "If clarification is needed, ask ONE focused user question and set question_field to "
        "one of material, force_n, stroke_min_mm, envelope_mm, material_properties. Prioritize "
        "force, then stroke, material, envelope when several are missing; uncertain modulus "
        "requires material_properties. Otherwise question_field and question must be null. "
        "issue_codes is an array drawn only from: " + ", ".join(ISSUES) + ". "
        "Abstain on contradictory requirements, minimum flexure thickness below 0.6 mm, "
        "package below 15 x 10 mm, out-of-plane certification, fatigue certification, "
        "zero force with positive stroke, or stress allowance above listed yield. "
        "Listed yield strengths: polypropylene 35 MPa, PETG 45 MPa, aluminum 240 MPa. "
        "Unknown batch modulus requires clarification. A ready specification requires "
        "material, force, stroke, envelope. Drift and stress limits are optional. "
        "Never invent absent values or assume a vague plastic grade. "
        "User request: " + request
    )
    if arm == "muse_raw_memory":
        prompt += "\n" + RAW_MEMORY
    elif arm == "muse_validated_memory":
        prompt += "\n" + VALIDATED_MEMORY
    return prompt


def normalize(raw):
    value = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    if not isinstance(value, dict) or set(value) != {"decision", "constraints", "missing", "question_field", "question", "issue_codes"}:
        raise ValueError("top-level schema")
    if value["decision"] not in {"proceed", "clarify", "abstain"}:
        raise ValueError("decision enum")
    c = value["constraints"]
    if not isinstance(c, dict) or set(c) != set(FIELDS):
        raise ValueError("constraint schema")
    if isinstance(c["material"], str):
        label = c["material"].strip().lower()
        c["material"] = "polypropylene" if label == "pp" else label
    if c["material"] is not None and c["material"] not in {"polypropylene", "petg", "aluminum"}:
        raise ValueError("material enum")
    for key in ("force_n", "stroke_min_mm", "drift_max_mm", "stress_max_mpa"):
        x = c[key]
        if x is not None and (isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or x < 0 or x > 1e5):
            raise ValueError("numeric field " + key)
    env = c["envelope_mm"]
    if env is not None and (not isinstance(env, list) or len(env) != 2 or
                            any(isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or x <= 0 or x > 1000 for x in env)):
        raise ValueError("envelope")
    if not isinstance(value["missing"], list) or len(value["missing"]) != len(set(value["missing"])) or any(x not in REQUIRED for x in value["missing"]):
        raise ValueError("missing fields")
    if value["question_field"] is not None and value["question_field"] not in QUESTION_FIELDS:
        raise ValueError("question field")
    if value["question"] is not None and (not isinstance(value["question"], str) or not 5 <= len(value["question"]) <= 300):
        raise ValueError("question text")
    if not isinstance(value["issue_codes"], list) or len(value["issue_codes"]) != len(set(value["issue_codes"])) or any(x not in ISSUES for x in value["issue_codes"]):
        raise ValueError("issue codes")
    if value["decision"] == "proceed" and (value["question_field"] is not None or value["question"] is not None or any(c[x] is None for x in REQUIRED)):
        raise ValueError("unsafe proceed")
    if value["decision"] == "clarify" and (value["question_field"] is None or value["question"] is None):
        raise ValueError("clarification lacks question")
    if value["decision"] == "abstain" and value["question_field"] is not None:
        raise ValueError("abstention asks question")
    return value


def deterministic(request):
    interpretation = compile_intent(request)
    action = clarification(interpretation)
    decisions = {"ready_for_static_beam_screen": "proceed", "needs_clarification": "clarify",
                 "contradictory": "abstain", "unsupported_physics": "abstain"}
    issues = []
    if "Package is below the supported beam geometry scale" in interpretation["contradictions"]:
        issues.append("package_below_scale")
    if "Positive actuation stroke requested with zero load" in interpretation["contradictions"]:
        issues.append("zero_force_positive_stroke")
    if "Stress limit exceeds listed material yield strength" in interpretation["contradictions"]:
        issues.append("stress_above_yield")
    if "fatigue" in interpretation["unsupported"]:
        issues.append("fatigue")
    return {"decision": decisions[interpretation["decision"]], "constraints": interpretation["constraints"],
            "missing": interpretation["missing"], "question_field": action.get("field"),
            "question": action.get("question"), "issue_codes": issues}


def metric(candidate, reference):
    if candidate is None:
        return {"decision_correct": False, "fields_correct": 0, "missing_correct": False,
                "question_field_correct": False, "issues_correct": False,
                "unsafe_assumptions": 6, "full_case": False}
    fields = 0
    unsafe = 0
    for key, expected in reference["constraints"].items():
        actual = candidate["constraints"][key]
        if expected is None and actual is not None:
            unsafe += 1
        if isinstance(expected, list):
            same = isinstance(actual, list) and len(actual) == 2 and all(abs(a-b) < 1e-6 for a,b in zip(actual, expected))
        elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
            same = isinstance(actual, (float, int)) and abs(actual-expected) < 1e-6
        else:
            same = actual == expected
        fields += int(same)
    decision = candidate["decision"] == reference["decision"]
    missing = set(candidate["missing"]) == set(reference["missing"])
    question = candidate["question_field"] == reference["question_field"]
    issues = set(candidate["issue_codes"]) == set(reference["issue_codes"])
    return {"decision_correct": decision, "fields_correct": fields,
            "missing_correct": missing, "question_field_correct": question,
            "issues_correct": issues, "unsafe_assumptions": unsafe,
            "full_case": decision and fields == 6 and missing and question and issues and unsafe == 0}


def muse(prompt, state):
    if sum(x["estimated_cost_usd"] for x in state["receipts"]) >= MAX_NEW_ESTIMATED_USD - .01:
        raise RuntimeError("Clarification benchmark cost ceiling reached")
    key = meta_key()
    if not key:
        raise RuntimeError("Meta API credential unavailable")
    request = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0, "reasoning_effort": "minimal", "max_completion_tokens": 1400}
    start = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=key, timeout=70).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    receipt = {"request_id": response.id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "request": request, "request_sha256": digest(request), "response": raw,
               "response_sha256": hashlib.sha256(raw.encode()).hexdigest(), "model": response.model,
               "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
               "estimated_cost_usd": (usage.prompt_tokens*.20+usage.completion_tokens*.80)/1e6,
               "actual_billed_cost_usd": "UNKNOWN", "latency_s": time.perf_counter()-start,
               "finish_reason": response.choices[0].finish_reason}
    return raw, receipt


def main():
    frozen = json.loads(FROZEN.read_text())
    assert digest({k:v for k,v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    state = json.loads(LEDGER.read_text()) if LEDGER.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(), "frozen_sha256": frozen["sha256"],
        "arms": ARM_ORDER, "results": {}, "receipts": []}
    if state["frozen_sha256"] != frozen["sha256"]:
        raise RuntimeError("Ledger bound to different task set")
    for case in frozen["cases"]:
        for arm in ARM_ORDER:
            ident = case["id"] + "/" + arm
            if ident in state["results"]:
                continue
            if arm == "deterministic":
                candidate, receipt_index, failure = deterministic(case["request"]), None, None
            else:
                raw, receipt = muse(prompt_for(case["request"], arm), state)
                receipt_index = len(state["receipts"])
                state["receipts"].append(receipt)
                save(state)
                try:
                    candidate, failure = normalize(raw), None
                except (ValueError, TypeError, KeyError) as exc:
                    candidate, failure = None, str(exc)
            result = {"candidate": candidate, "receipt_index": receipt_index,
                      "validation_failure": failure, "score": metric(candidate, case["reference"])}
            state["results"][ident] = result
            save(state)
            print(ident, result["score"], flush=True)
    state["status"] = "COMPLETE"
    state["new_estimated_cost_usd"] = sum(x["estimated_cost_usd"] for x in state["receipts"])
    save(state)
    print("COMPLETE", state["new_estimated_cost_usd"], flush=True)


if __name__ == "__main__":
    main()

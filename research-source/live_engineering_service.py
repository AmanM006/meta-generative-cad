"""Bounded, authenticated live Muse-to-beam engineering workflow.

The service scales one validated two-stage graph family within declared package
bounds. Every result is computed for the user's actual typed specification.
This is numerical screening, not fabrication certification or topology invention.
"""
import asyncio
import copy
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engineering_intent import MATERIALS, compile_intent
from open_ended_structural_discovery_engine import digest, evaluate
from r9_repair_policy import failure_metrics, measured_direction, mutate, parse_repair, repair_prompt


def call_muse_live(text):
    """Load benchmark model code only when an authenticated live run begins."""
    from run_clarification_20 import muse, prompt_for
    return muse(prompt_for(text, "muse_cold"), {"receipts": []})


def normalize_live(raw):
    from run_clarification_20 import normalize
    return normalize(raw)


def call_muse_repair_live(prompt):
    from run_clarification_20 import muse
    return muse(prompt, {"receipts": []})

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / ".runtime_live"
PRIVATE.mkdir(exist_ok=True)
BUDGET_FILE = PRIVATE / "budget.json"
SOURCE = ROOT / "fresh_evidence/intent_spec_confirmatory_results.json"
MAX_MODEL_CALLS = 16
MAX_MODEL_ESTIMATED_USD = .10
MAX_ACTIVE_JOBS = 2
MAX_STARTS_PER_MINUTE = 4
CLARIFICATION_TTL_SECONDS = 15 * 60
THICKNESSES_MM = (.6, .7, .8, .9, 1.0)
JOINT_CORNERS = (("low_low", .95, .90), ("low_high", .95, 1.10),
                 ("high_low", 1.05, .90), ("high_high", 1.05, 1.10))
PREFIX = {"force_n": "force", "stroke_min_mm": "stroke", "material": "material",
          "envelope_mm": "package", "material_properties": "measured modulus",
          "drift_max_mm": "drift under", "stress_max_mpa": "stress under"}
QUESTIONS = {"drift_max_mm": "What maximum lateral drift, in mm, is acceptable?",
             "stress_max_mpa": "What maximum stress, in MPa, is acceptable?",
             "material_properties": "What measured elastic modulus, in GPa, applies to this batch?"}

router = APIRouter(prefix="/api/live", tags=["live-engineering"])
JOBS = {}
START_TIMES = []
BUDGET_LOCK = asyncio.Lock()
MODEL_SEMAPHORE = asyncio.Semaphore(1)
SOLVER_SEMAPHORE = asyncio.Semaphore(1)


class StartRequest(BaseModel):
    request_text: str = Field(min_length=10, max_length=1000)
    access_code: str = Field(min_length=8, max_length=100)
    repair_mode: Literal["deterministic", "muse_directed", "muse_validated_memory", "muse_casm_repair"] = "deterministic"


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=250)
    access_code: str = Field(min_length=8, max_length=100)
    job_token: str = Field(min_length=32, max_length=100)


class StatusRequest(BaseModel):
    access_code: str = Field(min_length=8, max_length=100)
    job_token: str = Field(min_length=32, max_length=100)


def now():
    return datetime.now(timezone.utc).isoformat()


def enabled():
    return bool(os.environ.get("MODEL_API_KEY") and os.environ.get("LIVE_DEMO_ACCESS_CODE"))


def authorize(code):
    if not enabled():
        raise HTTPException(status_code=503, detail="Live engineering is not configured")
    if not hmac.compare_digest(code, os.environ["LIVE_DEMO_ACCESS_CODE"]):
        raise HTTPException(status_code=403, detail="Invalid live access code")


def authorize_job(job, token):
    candidate = hashlib.sha256(token.encode()).hexdigest()
    if not hmac.compare_digest(candidate, job["job_token_sha256"]):
        raise HTTPException(status_code=403, detail="Invalid job token")


def expire_idle_clarifications():
    clock = time.time()
    for job in JOBS.values():
        if job["status"] == "needs_clarification" and clock - job.get("last_action_epoch", clock) > CLARIFICATION_TTL_SECONDS:
            job["status"] = "expired"
            event(job, "clarification_expired", "Restart after 15 minutes without an answer")


def persist(job):
    path = PRIVATE / (job["id"] + ".json")
    temporary = PRIVATE / (job["id"] + ".tmp")
    temporary.write_text(json.dumps(job, indent=2))
    temporary.replace(path)


def event(job, name, detail):
    job["events"].append({"at_utc": now(), "step": name, "detail": detail})
    job["updated_utc"] = now()
    persist(job)


def public(job):
    view = {k: v for k, v in job.items() if k not in {"receipts", "access_code", "full_text", "job_token_sha256", "last_action_epoch"}}
    view["provenance"] = [{"model": r["model"], "request_id": r["request_id"],
                           "request_sha256": r["request_sha256"],
                           "response_sha256": r["response_sha256"],
                           "estimated_cost_usd": r["estimated_cost_usd"]}
                          for r in job["receipts"]]
    return view


def budget():
    if BUDGET_FILE.exists():
        return json.loads(BUDGET_FILE.read_text())
    return {"reserved_calls": 0, "estimated_spend_usd": 0.0}


def persist_budget(value):
    temporary = PRIVATE / "budget.tmp"
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(BUDGET_FILE)


async def reserve_model_call():
    async with BUDGET_LOCK:
        value = budget()
        if value["reserved_calls"] >= MAX_MODEL_CALLS or value["estimated_spend_usd"] >= MAX_MODEL_ESTIMATED_USD:
            raise RuntimeError("Live model budget exhausted")
        value["reserved_calls"] += 1
        persist_budget(value)


async def settle_model_call(receipt):
    async with BUDGET_LOCK:
        value = budget()
        value["estimated_spend_usd"] += receipt["estimated_cost_usd"]
        persist_budget(value)


def grounded(candidate, raw_text):
    """Reject model values that have no matching number and unit in the text."""
    import re
    text = raw_text.lower().replace("μ", "µ")
    c = candidate["constraints"]
    material = c["material"]
    if material is not None:
        names = {"polypropylene": ("polypropylene", "pp"), "petg": ("petg",), "aluminum": ("aluminum",)}[material]
        if not any(re.search(r"\b"+re.escape(name)+r"\b", text) for name in names):
            return False, "Model material is absent from user text"
    numbers = {"n": [], "mm": [], "mpa": []}
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(mn|n|mm|µm|um|micrometers?|mpa)\b", text):
        number = float(value)
        if unit == "mn":
            numbers["n"].append(number/1000)
        elif unit == "n":
            numbers["n"].append(number)
        elif unit in ("µm", "um", "micrometer", "micrometers"):
            numbers["mm"].append(number/1000)
        else:
            numbers[unit].append(number)
    for field, unit in (("force_n", "n"), ("stroke_min_mm", "mm"),
                        ("drift_max_mm", "mm"), ("stress_max_mpa", "mpa")):
        value = c[field]
        if value is not None and not any(abs(value-x) < 1e-5 for x in numbers[unit]):
            return False, "Model value lacks explicit unit-backed text: " + field
    envelope = c["envelope_mm"]
    if envelope is not None:
        pairs = re.findall(r"(\d+(?:\.\d+)?)\s*(?:mm)?\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm\b", text)
        if not any(all(abs(float(x)-y) < 1e-5 for x,y in zip(pair,envelope)) for pair in pairs):
            return False, "Model envelope lacks explicit width × height"
    return True, None


def compiled_from_candidate(candidate, text):
    safety = compile_intent(text)
    if safety["decision"] in {"contradictory", "unsupported_physics"}:
        raise ValueError("Independent safety gate: " + safety["decision"])
    okay, reason = grounded(candidate, text)
    if not okay:
        raise ValueError(reason)
    for field in ("material", "force_n", "stroke_min_mm", "envelope_mm", "drift_max_mm", "stress_max_mpa"):
        independently_parsed = safety["constraints"].get(field)
        model_value = candidate["constraints"].get(field)
        if independently_parsed is not None and model_value is not None and independently_parsed != model_value:
            raise ValueError("Model disagrees with independent parser: " + field)
    preflight_supported(candidate["constraints"], safety.get("material_properties", {}).get("measured_E_gpa"))
    return {"decision": candidate["decision"], "constraints": candidate["constraints"],
            "missing": candidate["missing"], "question_field": candidate["question_field"],
            "issue_codes": candidate["issue_codes"],
            "measured_E_gpa": safety.get("material_properties", {}).get("measured_E_gpa"),
            "provenance": "live_muse_with_independent_safety_gate"}


def preflight_supported(c, measured_E_gpa=None):
    if c["material"] is not None and c["material"] not in ("polypropylene", "petg"):
        raise ValueError("Supported live materials are polypropylene and PETG")
    envelope = c["envelope_mm"]
    if envelope is not None and not (55 <= envelope[0] <= 110 and 35 <= envelope[1] <= 75):
        raise ValueError("Supported package width is 55–110 mm and height is 35–75 mm")
    if c["force_n"] is not None and not (.5 <= c["force_n"] <= 10):
        raise ValueError("Supported static force is 0.5–10 N")
    if c["stroke_min_mm"] is not None and not (.3 <= c["stroke_min_mm"] <= 2.5):
        raise ValueError("Supported stroke is 0.3–2.5 mm")
    if c["drift_max_mm"] is not None and not (.005 <= c["drift_max_mm"] <= .2):
        raise ValueError("Supported drift limit is 0.005–0.2 mm")
    if c["stress_max_mpa"] is not None and (c["stress_max_mpa"] <= 0 or
            (c["material"] in ("polypropylene", "petg") and
             c["stress_max_mpa"] > MATERIALS[c["material"]]["yield_strength_pa"]/1e6)):
        raise ValueError("Stress limit must be positive and no greater than nominal material yield")
    if measured_E_gpa is not None and not (.2 <= measured_E_gpa <= 10):
        raise ValueError("Measured modulus outside supported polymer screen range")


async def call_model(job):
    try:
        async with MODEL_SEMAPHORE:
            await reserve_model_call()
            event(job, "model_request", "Calling Meta Muse with a 60 s timeout")
            raw, receipt = await asyncio.wait_for(
                asyncio.to_thread(call_muse_live, job["full_text"]),
                timeout=65)
            job["receipts"].append(receipt)
            await settle_model_call(receipt)
            event(job, "model_receipt", {"request_id": receipt["request_id"],
                                          "estimated_cost_usd": receipt["estimated_cost_usd"]})
            candidate = normalize_live(raw)
            job["specification"] = compiled_from_candidate(candidate, job["full_text"])
            job["interpretation"] = candidate
            event(job, "typed_interpretation", {"decision": candidate["decision"],
                                                "constraints": candidate["constraints"],
                                                "issue_codes": candidate["issue_codes"]})
        if candidate["decision"] == "abstain":
            job["status"] = "abstained"
            event(job, "abstain", "Model or independent gate rejected the request")
        elif candidate["decision"] == "clarify":
            if len(job["receipts"]) >= 2:
                job["status"] = "needs_manual_revision"
                event(job, "clarification_limit", "Two live model calls used; revise and restart")
            else:
                job["question"] = {"field": candidate["question_field"],
                                   "text": candidate["question"], "source": "live_muse"}
                job["status"] = "needs_clarification"
                event(job, "clarification_question", job["question"])
        else:
            await ready_or_ask(job)
    except Exception as exc:
        job["status"] = "error"
        job["error"] = "Live model or validation failed (" + type(exc).__name__ + ")"
        event(job, "error", job["error"])


async def ready_or_ask(job):
    c = job["specification"]["constraints"]
    for field in ("drift_max_mm", "stress_max_mpa"):
        if c[field] is None:
            job["question"] = {"field": field, "text": QUESTIONS[field], "source": "deterministic_solver_requirement"}
            job["status"] = "needs_clarification"
            event(job, "clarification_question", job["question"])
            return
    safety = compile_intent(job["full_text"])
    if "material_properties" in safety["missing"]:
        job["question"] = {"field": "material_properties", "text": QUESTIONS["material_properties"],
                           "source": "deterministic_solver_requirement"}
        job["status"] = "needs_clarification"
        event(job, "clarification_question", job["question"])
        return
    job["status"] = "screening"
    event(job, "solver_queued", "Bounded two-stage beam screen queued")
    asyncio.create_task(run_solver(job))


def task_for(spec):
    c = spec["constraints"]
    if c["material"] not in ("polypropylene", "petg"):
        raise ValueError("Live template supports polypropylene or PETG only")
    envelope = c["envelope_mm"]
    if not envelope or not (55 <= envelope[0] <= 110 and 35 <= envelope[1] <= 75):
        raise ValueError("Live family supports 55–110 mm width and 35–75 mm height")
    if not (.5 <= c["force_n"] <= 10 and .3 <= c["stroke_min_mm"] <= 2.5):
        raise ValueError("Load or stroke outside live template bounds")
    if not (.005 <= c["drift_max_mm"] <= .2 and 0 < c["stress_max_mpa"] <= MATERIALS[c["material"]]["yield_strength_pa"]/1e6):
        raise ValueError("Drift or stress limit outside supported bounds")
    material = dict(MATERIALS[c["material"]], depth_m=.01)
    if spec["measured_E_gpa"] is not None:
        if not (.2 <= spec["measured_E_gpa"] <= 10):
            raise ValueError("Measured modulus outside supported polymer screen range")
        material["E_pa"] = spec["measured_E_gpa"]*1e9
    return {"envelope_m": [envelope[0]/1000, envelope[1]/1000], "material_properties": material,
            "force_n": c["force_n"], "stroke_min_mm": c["stroke_min_mm"],
            "drift_max_mm": c["drift_max_mm"], "stress_max_mpa": c["stress_max_mpa"],
            "min_flexure_thickness_m": .0006}


def proposal_for_envelope(base, envelope_mm):
    """Scale positions and stage heights; retain evaluated flexure thicknesses."""
    proposal = copy.deepcopy(base)
    sx, sy = envelope_mm[0] / 75, envelope_mm[1] / 50
    proposal["anchors"] = [[x*sx, y*sy] for x, y in proposal["anchors"]]
    for stage in proposal["stages"]:
        stage["center"] = [stage["center"][0]*sx, stage["center"][1]*sy]
        stage["height"] *= sy
    return proposal


async def evaluate_bounded(proposal, task, density):
    return await asyncio.wait_for(asyncio.to_thread(evaluate, proposal, task, mesh_density=density), timeout=180)


async def measure_repair_action(candidate, task, failed):
    """Common FEA budget and physical gates for model and deterministic actions."""
    corner_task = copy.deepcopy(task)
    corner_task["material_properties"]["E_pa"] *= failed["modulus_scale"]
    corner_candidate = copy.deepcopy(candidate)
    for edge in corner_candidate["connections"]:
        edge["thickness"] *= failed["thickness_scale"]
    measured_corner = await evaluate_bounded(corner_candidate, corner_task, 48)
    baseline_has_metrics = all(k in failed["result"] for k in ("stroke_mm", "absolute_drift_mm"))
    directions = ({
        "stroke": measured_direction(failed["result"]["stroke_mm"], measured_corner["stroke_mm"]),
        "drift": measured_direction(failed["result"]["absolute_drift_mm"], measured_corner["absolute_drift_mm"]),
    } if baseline_has_metrics and all(k in measured_corner for k in ("stroke_mm", "absolute_drift_mm"))
        else {"stroke": "unscorable", "drift": "unscorable"})
    coarse = await evaluate_bounded(candidate, task, 16)
    measured = {"candidate": {"proposal": candidate, "coarse": coarse,
                               "fine": None, "joint_corners": []},
                "measured_failed_scenario_after": measured_corner,
                "measured_directions": directions,
                "verdict": "rejected_by_coarse_fea"}
    if coarse["feasible"]:
        fine = await evaluate_bounded(candidate, task, 48)
        measured["candidate"]["fine"] = fine
        measured["verdict"] = "rejected_by_fine_fea"
        if fine["feasible"]:
            for name, tscale, escale in JOINT_CORNERS:
                if name == failed["name"]:
                    result = measured_corner
                else:
                    variant = copy.deepcopy(candidate)
                    variant_task = copy.deepcopy(task)
                    for edge in variant["connections"]:
                        edge["thickness"] *= tscale
                    variant_task["material_properties"]["E_pa"] *= escale
                    result = await evaluate_bounded(variant, variant_task, 48)
                measured["candidate"]["joint_corners"].append({"name": name, "result": result})
            measured["verdict"] = ("robust_beam_pass" if all(x["result"]["feasible"]
                                   for x in measured["candidate"]["joint_corners"]) else
                                   "rejected_by_joint_uncertainty")
    return measured


async def attempt_muse_repair(job, baseline_proposal, task, baseline_trial):
    """One model-chosen, independently compiled and measured corrective experiment."""
    failed = next(x for x in baseline_trial["joint_corners"] if not x["result"]["feasible"])
    measured_failure = failure_metrics(failed["result"], failed["task"])
    record = {"baseline_thickness_mm": baseline_trial["thickness_mm"],
              "failed_scenario": failed["name"], "measured_failure": measured_failure,
              "candidate": None, "prediction_check": None, "verdict": "not_run"}
    job["repair_attempt"] = record
    event(job, "measured_failure_sent_to_muse", measured_failure)
    if len(job["receipts"]) >= 3:
        record["verdict"] = "per_job_model_call_limit"
        event(job, "repair_rejected", record["verdict"])
        return None
    prompt = repair_prompt(job["specification"], measured_failure,
                           baseline_trial["thickness_mm"],
                           validated_memory=job["repair_mode"] == "muse_validated_memory",
                           casm_memory=job["repair_mode"] == "muse_casm_repair")
    try:
        async with MODEL_SEMAPHORE:
            await reserve_model_call()
            event(job, "repair_model_request", "One bounded Meta Muse corrective experiment")
            raw, receipt = await asyncio.wait_for(asyncio.to_thread(call_muse_repair_live, prompt), timeout=65)
            job["receipts"].append(receipt)
            await settle_model_call(receipt)
            record["model_request_id"] = receipt["request_id"]
            event(job, "repair_model_receipt", {"request_id": receipt["request_id"],
                                                 "estimated_cost_usd": receipt["estimated_cost_usd"]})
        choice = parse_repair(raw, measured_failure["failed_gates"])
        candidate = mutate(baseline_proposal, choice["action"])
        record["hypothesis"] = choice
        record["candidate_sha256"] = digest(candidate)
        event(job, "repair_hypothesis", {"hypothesis": choice,
                                          "candidate_sha256": record["candidate_sha256"]})
        measured = await measure_repair_action(candidate, task, failed)
        record["measured_failed_scenario_after"] = measured["measured_failed_scenario_after"]
        record["candidate"] = measured["candidate"]
        record["verdict"] = measured["verdict"]
        directions = measured["measured_directions"]
        record["prediction_check"] = {
            "predicted": {"stroke": choice["predicted_stroke_direction"],
                          "drift": choice["predicted_drift_direction"]},
            "measured": directions,
            "both_correct": (choice["predicted_stroke_direction"] == directions["stroke"] and
                             choice["predicted_drift_direction"] == directions["drift"])
                            if directions["stroke"] != "unscorable" else None,
        }
        event(job, "repair_prediction_measured", {"actual_failed_corner": record["measured_failed_scenario_after"],
                                                  "direction_check": record["prediction_check"]})
        event(job, "repair_verdict", {"verdict": record["verdict"],
                                      "prediction_check": record["prediction_check"]})
        return record if record["verdict"] == "robust_beam_pass" else None
    except Exception as exc:
        record["verdict"] = "invalid_or_failed_repair_" + type(exc).__name__
        event(job, "repair_rejected", record["verdict"])
        return None


async def run_solver(job):
    try:
        async with SOLVER_SEMAPHORE:
            task = task_for(job["specification"])
            source = json.loads(SOURCE.read_text())
            source_base = source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
            base = proposal_for_envelope(source_base, job["specification"]["constraints"]["envelope_mm"])
            job["solver_task"] = task
            job["geometry_source_sha256"] = digest(source_base)
            job["evaluated_geometry_sha256"] = digest(base)
            job["geometry_family"] = "scaled_two_stage_template; thickness optimized; topology fixed"
            job["trials"] = []
            selected = None
            selected_design = None
            selected_proposal = None
            selection_source = None
            nominal_first = None
            repair_attempted = False
            for thickness in THICKNESSES_MM:
                candidate = copy.deepcopy(base)
                for edge in candidate["connections"]:
                    edge["thickness"] = thickness/1000
                coarse = await evaluate_bounded(candidate, task, 16)
                trial = {"thickness_mm": thickness, "coarse": coarse, "fine": None, "joint_corners": []}
                job["trials"].append(trial)
                event(job, "coarse_solver", {"thickness_mm": thickness, "feasible": coarse["feasible"],
                                              "gates": coarse.get("gates"), "stroke_mm": coarse.get("stroke_mm"),
                                              "absolute_drift_mm": coarse.get("absolute_drift_mm")})
                if not coarse["feasible"]:
                    continue
                fine = await evaluate_bounded(candidate, task, 48)
                trial["fine"] = fine
                event(job, "fine_solver", {"thickness_mm": thickness, "feasible": fine["feasible"],
                                            "gates": fine.get("gates"), "stroke_mm": fine.get("stroke_mm"),
                                            "absolute_drift_mm": fine.get("absolute_drift_mm")})
                if not fine["feasible"]:
                    continue
                if nominal_first is None:
                    nominal_first = thickness
                for name, tscale, escale in JOINT_CORNERS:
                    variant = copy.deepcopy(candidate)
                    variant_task = copy.deepcopy(task)
                    for edge in variant["connections"]:
                        edge["thickness"] *= tscale
                    variant_task["material_properties"]["E_pa"] *= escale
                    result = await evaluate_bounded(variant, variant_task, 48)
                    trial["joint_corners"].append({"name": name, "thickness_scale": tscale,
                                                   "modulus_scale": escale, "task": variant_task,
                                                   "result": result})
                    event(job, "joint_uncertainty", {"thickness_mm": thickness, "scenario": name,
                                                     "feasible": result["feasible"],
                                                     "gates": result.get("gates")})
                if all(x["result"]["feasible"] for x in trial["joint_corners"]):
                    selected = thickness
                    selected_design = f"uniform {thickness:.1f} mm flexures"
                    selected_proposal = copy.deepcopy(candidate)
                    selection_source = ("deterministic_fallback_after_muse" if repair_attempted else
                                        "deterministic_sweep")
                    break
                if job.get("repair_mode", "deterministic") != "deterministic" and not repair_attempted:
                    repair_attempted = True
                    repaired = await attempt_muse_repair(job, candidate, task, trial)
                    if repaired is not None:
                        action = repaired["hypothesis"]["action"]
                        selected = round(thickness + .1, 1) if action == "uniform_plus_0p1" else None
                        selected_design = f"{thickness:.1f} mm base with {action}"
                        selected_proposal = repaired["candidate"]["proposal"]
                        selection_source = "muse_directed_proposal_independently_verified"
                        break
            job["nominal_first_mm"] = nominal_first
            job["selected_mm"] = selected
            job["selected_design"] = selected_design
            job["selected_proposal"] = selected_proposal
            job["selection_source"] = selection_source
            job["status"] = "completed" if selected_design is not None else "unresolved"
            job["verdict"] = ("joint_corner_beam_pass" if selected_design is not None else
                              "no_joint_corner_pass_within_five_candidates")
            event(job, "final_verdict", {"verdict": job["verdict"], "selected_mm": selected,
                                          "selected_design": selected_design,
                                          "selection_source": selection_source,
                                          "scope": "2D beam model; clearance and fabrication unverified"})
    except Exception as exc:
        job["status"] = "error"
        job["error"] = "Beam screen failed (" + type(exc).__name__ + ")"
        event(job, "error", job["error"])


@router.get("/capabilities")
async def capabilities():
    value = budget()
    return {"enabled": enabled(), "solver_scope": "PP or PETG; 55–110 × 35–75 mm scaled two-stage family; 2D nonlinear beam screen",
            "max_model_calls_per_instance": MAX_MODEL_CALLS,
            "remaining_model_calls_this_instance": max(0, MAX_MODEL_CALLS-value["reserved_calls"]),
            "estimated_spend_this_instance_usd": value["estimated_spend_usd"],
            "requires_access_code": True, "execution_mode": "LIVE_IF_ENABLED"}


@router.post("/start")
async def start(request: StartRequest):
    authorize(request.access_code)
    expire_idle_clarifications()
    clock = time.monotonic()
    START_TIMES[:] = [t for t in START_TIMES if clock - t < 60]
    if len(START_TIMES) >= MAX_STARTS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Live start rate limit reached")
    active = sum(x["status"] in {"model_running", "needs_clarification", "screening"} for x in JOBS.values())
    if active >= MAX_ACTIVE_JOBS:
        raise HTTPException(status_code=429, detail="Live engineering capacity reached")
    text = request.request_text.strip()
    safety = compile_intent(text)
    if safety["decision"] in {"contradictory", "unsupported_physics"}:
        raise HTTPException(status_code=422, detail="Independent safety gate: " + safety["decision"])
    try:
        preflight_supported(safety["constraints"], safety.get("material_properties", {}).get("measured_E_gpa"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    START_TIMES.append(clock)
    ident = uuid.uuid4().hex
    token = secrets.token_urlsafe(32)
    job = {"id": ident, "created_utc": now(), "updated_utc": now(),
           "job_token_sha256": hashlib.sha256(token.encode()).hexdigest(),
           "last_action_epoch": time.time(),
           "status": "model_running", "request_text": text, "full_text": text,
           "repair_mode": request.repair_mode, "repair_attempt": None,
           "execution_mode": "LIVE_MUSE_LIVE_BEAM_FEA", "events": [], "receipts": [],
           "interpretation": None, "specification": None, "question": None,
           "answer_history": [], "trials": [], "error": None}
    JOBS[ident] = job
    event(job, "request_accepted", "Live Muse interpretation queued")
    asyncio.create_task(call_model(job))
    return {**public(job), "job_token": token}


@router.post("/{job_id}/answer")
async def answer(job_id: str, request: AnswerRequest):
    authorize(request.access_code)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Live job unavailable")
    authorize_job(job, request.job_token)
    if job["status"] != "needs_clarification" or not job["question"]:
        raise HTTPException(status_code=409, detail="Job is not waiting for an answer")
    field = job["question"]["field"]
    text = request.answer.strip()
    job["last_action_epoch"] = time.time()
    job["answer_history"].append({"field": field, "answer": text, "at_utc": now(),
                                  "question_source": job["question"]["source"]})
    job["full_text"] += " " + PREFIX[field] + " " + text
    event(job, "user_answer", {"field": field, "answer": text})
    source = job["question"]["source"]
    job["question"] = None
    if source == "live_muse":
        job["status"] = "model_running"
        asyncio.create_task(call_model(job))
    else:
        parsed = compile_intent(job["full_text"])
        if parsed["decision"] in {"contradictory", "unsupported_physics"}:
            job["status"] = "abstained"
            event(job, "independent_safety_gate", parsed["decision"])
        else:
            value = parsed["constraints"].get(field) if field != "material_properties" else parsed["material_properties"]["measured_E_gpa"]
            if value is None:
                job["status"] = "needs_clarification"
                job["question"] = {"field": field, "text": QUESTIONS[field], "source": source}
                event(job, "answer_not_parsed", job["question"])
            else:
                if field == "material_properties":
                    job["specification"]["measured_E_gpa"] = value
                else:
                    job["specification"]["constraints"][field] = value
                await ready_or_ask(job)
    return public(job)


@router.post("/{job_id}/status")
async def status(job_id: str, request: StatusRequest):
    authorize(request.access_code)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Live job unavailable or interrupted by service restart")
    authorize_job(job, request.job_token)
    return public(job)

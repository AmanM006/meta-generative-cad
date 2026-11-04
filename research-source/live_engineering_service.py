"""Bounded, authenticated live Muse-to-beam engineering workflow.

The service uses one stored 75 x 50 mm two-stage graph family. Every result is
computed for the user's actual typed specification. It is numerical screening,
not a fabricated-device certification or a topology invention claim.
"""
import asyncio
import copy
import hmac
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engineering_intent import MATERIALS, compile_intent
from open_ended_structural_discovery_engine import digest, evaluate


def call_muse_live(text):
    """Load benchmark model code only when an authenticated live run begins."""
    from run_clarification_20 import muse, prompt_for
    return muse(prompt_for(text, "muse_cold"), {"receipts": []})


def normalize_live(raw):
    from run_clarification_20 import normalize
    return normalize(raw)

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / ".runtime_live"
PRIVATE.mkdir(exist_ok=True)
BUDGET_FILE = PRIVATE / "budget.json"
SOURCE = ROOT / "fresh_evidence/intent_spec_confirmatory_results.json"
MAX_MODEL_CALLS = 16
MAX_MODEL_ESTIMATED_USD = .10
MAX_ACTIVE_JOBS = 2
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
BUDGET_LOCK = asyncio.Lock()
MODEL_SEMAPHORE = asyncio.Semaphore(1)
SOLVER_SEMAPHORE = asyncio.Semaphore(1)


class StartRequest(BaseModel):
    request_text: str = Field(min_length=10, max_length=1000)
    access_code: str = Field(min_length=8, max_length=100)


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=250)
    access_code: str = Field(min_length=8, max_length=100)


class StatusRequest(BaseModel):
    access_code: str = Field(min_length=8, max_length=100)


def now():
    return datetime.now(timezone.utc).isoformat()


def enabled():
    return bool(os.environ.get("MODEL_API_KEY") and os.environ.get("LIVE_DEMO_ACCESS_CODE"))


def authorize(code):
    if not enabled():
        raise HTTPException(status_code=503, detail="Live engineering is not configured")
    if not hmac.compare_digest(code, os.environ["LIVE_DEMO_ACCESS_CODE"]):
        raise HTTPException(status_code=403, detail="Invalid live access code")


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
    view = {k: v for k, v in job.items() if k not in {"receipts", "access_code", "full_text"}}
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
    return {"decision": candidate["decision"], "constraints": candidate["constraints"],
            "missing": candidate["missing"], "question_field": candidate["question_field"],
            "issue_codes": candidate["issue_codes"],
            "measured_E_gpa": safety.get("material_properties", {}).get("measured_E_gpa"),
            "provenance": "live_muse_with_independent_safety_gate"}


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
    if c["envelope_mm"] != [75, 50]:
        raise ValueError("Live template supports a 75 × 50 mm package only")
    if not (.5 <= c["force_n"] <= 10 and .3 <= c["stroke_min_mm"] <= 2.5):
        raise ValueError("Load or stroke outside live template bounds")
    if not (.005 <= c["drift_max_mm"] <= .2 and 0 < c["stress_max_mpa"] <= MATERIALS[c["material"]]["yield_strength_pa"]/1e6):
        raise ValueError("Drift or stress limit outside supported bounds")
    material = dict(MATERIALS[c["material"]], depth_m=.01)
    if spec["measured_E_gpa"] is not None:
        material["E_pa"] = spec["measured_E_gpa"]*1e9
    return {"envelope_m": [.075,.05], "material_properties": material,
            "force_n": c["force_n"], "stroke_min_mm": c["stroke_min_mm"],
            "drift_max_mm": c["drift_max_mm"], "stress_max_mpa": c["stress_max_mpa"],
            "min_flexure_thickness_m": .0006}


async def evaluate_bounded(proposal, task, density):
    return await asyncio.wait_for(asyncio.to_thread(evaluate, proposal, task, mesh_density=density), timeout=75)


async def run_solver(job):
    try:
        async with SOLVER_SEMAPHORE:
            task = task_for(job["specification"])
            source = json.loads(SOURCE.read_text())
            base = source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
            job["solver_task"] = task
            job["geometry_source_sha256"] = digest(base)
            job["trials"] = []
            selected = None
            nominal_first = None
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
                    break
            job["nominal_first_mm"] = nominal_first
            job["selected_mm"] = selected
            job["status"] = "completed" if selected is not None else "unresolved"
            job["verdict"] = ("joint_corner_beam_pass" if selected is not None else
                              "no_joint_corner_pass_within_five_candidates")
            event(job, "final_verdict", {"verdict": job["verdict"], "selected_mm": selected,
                                          "scope": "2D beam model; clearance and fabrication unverified"})
    except Exception as exc:
        job["status"] = "error"
        job["error"] = "Beam screen failed (" + type(exc).__name__ + ")"
        event(job, "error", job["error"])


@router.get("/capabilities")
async def capabilities():
    value = budget()
    return {"enabled": enabled(), "solver_scope": "PP or PETG, 75 × 50 mm, 2D nonlinear beam screen",
            "max_model_calls_per_instance": MAX_MODEL_CALLS,
            "remaining_model_calls_this_instance": max(0, MAX_MODEL_CALLS-value["reserved_calls"]),
            "estimated_spend_this_instance_usd": value["estimated_spend_usd"],
            "requires_access_code": True, "execution_mode": "LIVE_IF_ENABLED"}


@router.post("/start")
async def start(request: StartRequest):
    authorize(request.access_code)
    active = sum(x["status"] in {"model_running", "needs_clarification", "screening"} for x in JOBS.values())
    if active >= MAX_ACTIVE_JOBS:
        raise HTTPException(status_code=429, detail="Live engineering capacity reached")
    text = request.request_text.strip()
    safety = compile_intent(text)
    if safety["decision"] in {"contradictory", "unsupported_physics"}:
        raise HTTPException(status_code=422, detail="Independent safety gate: " + safety["decision"])
    ident = uuid.uuid4().hex
    job = {"id": ident, "created_utc": now(), "updated_utc": now(),
           "status": "model_running", "request_text": text, "full_text": text,
           "execution_mode": "LIVE_MUSE_LIVE_BEAM_FEA", "events": [], "receipts": [],
           "interpretation": None, "specification": None, "question": None,
           "answer_history": [], "trials": [], "error": None}
    JOBS[ident] = job
    event(job, "request_accepted", "Live Muse interpretation queued")
    asyncio.create_task(call_model(job))
    return public(job)


@router.post("/{job_id}/answer")
async def answer(job_id: str, request: AnswerRequest):
    authorize(request.access_code)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Live job unavailable")
    if job["status"] != "needs_clarification" or not job["question"]:
        raise HTTPException(status_code=409, detail="Job is not waiting for an answer")
    field = job["question"]["field"]
    text = request.answer.strip()
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
    return public(job)

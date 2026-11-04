"""FastAPI Autonomous Engineering Orchestrator Backend for Neodustria.

Connects:
Next.js Studio -> stored Muse evidence or deterministic input compilation ->
Geometry Compiler -> Nonlinear Corotational FEA -> Stability Audit -> 3D Solid GLB.
"""

import os
import sys
import json
import time
import uuid
import asyncio
import copy
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from engineering_intent import compile_intent, clarification

# Ensure path to local engineering modules
PROJECT_DIR = Path(__file__).resolve().parent
ENGINEERING_DIR = PROJECT_DIR / "engineering_runtime"
sys.path.insert(0, str(ENGINEERING_DIR))

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver, NonlinearConvergenceError
from generate_fea_solids import FEASolidRenderer

app = FastAPI(title="Neodustria Autonomous Engineering Orchestrator", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACT_DIR = PROJECT_DIR / "artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)
RUNS_DB_FILE = ARTIFACT_DIR / "runs_ledger.json"
app.mount("/artifacts", StaticFiles(directory=ARTIFACT_DIR), name="artifacts")
HOSTED_DEMO = bool(os.environ.get("RENDER_SERVICE_ID"))
if HOSTED_DEMO:
    shutil.copyfile(ENGINEERING_DIR / "verified_hero_replay.glb", ARTIFACT_DIR / "verified_hero_replay.glb")
RUNS_STATE: Dict[str, Dict[str, Any]] = {}
RUN_EVENT_QUEUES: Dict[str, asyncio.Queue] = {}

class DesignRequest(BaseModel):
    stroke_target_mm: float = 3.0
    load_fy_n: float = 5.0
    max_stress_mpa: float = 25.0
    mode: str = "replay_hero"  # Options: "replay_hero", "replay_p0", "replay_call3", "dry_run", "live_muse"
    topology_hint: Optional[str] = "compound_folded_flexure"

class IntentRequest(BaseModel):
    request_text: str = ""
    mode: str = "deterministic"
    example_id: Optional[str] = None

INTENT_EXAMPLES = {"C01", "C02", "C09", "C12"}
INTENT_BENCHMARK = PROJECT_DIR / "fresh_evidence/intent_spec_confirmatory_frozen.json"
INTENT_RESULTS = PROJECT_DIR / "fresh_evidence/intent_spec_confirmatory_results.json"
INTENT_REPAIR = PROJECT_DIR / "fresh_evidence/intent_c01_drift_repair.json"
INTENT_ROBUSTNESS = PROJECT_DIR / "fresh_evidence/intent_c01_robustness.json"
INTENT_ROBUST_SEARCH = PROJECT_DIR / "fresh_evidence/intent_c01_robust_search.json"
CLARIFICATION_BENCHMARK = PROJECT_DIR / "fresh_evidence/clarification_20_frozen.json"
CLARIFICATION_RESULTS = PROJECT_DIR / "fresh_evidence/clarification_20_results.json"
CLARIFICATION_EXAMPLES = {"Q02", "Q03", "Q04", "Q12", "Q15"}
CLARIFICATION_LOOPS = PROJECT_DIR / "fresh_evidence/clarification_3_scripted_loops.json"
LOOP_EXAMPLES = {"Q02", "Q03", "Q04"}
LOCAL_LIVE_RECORD = PROJECT_DIR / "fresh_evidence/live_clarification_operator_run.json"
LOCAL_LIVE_AUDIT = PROJECT_DIR / "fresh_evidence/live_clarification_audit.json"

def intent_plan(interpretation):
    decision = interpretation["decision"]
    if decision == "ready_for_static_beam_screen":
        return ["Compile two-stage candidate geometry", "Run nonlinear beam FEA",
                "Check stroke, absolute drift, stress, stability and deformed envelope",
                "Refine mesh before any physical claim"]
    if decision == "needs_clarification":
        return ["Ask for: " + ", ".join(interpretation.get("missing", [])),
                "Do not run FEA until required inputs are known"]
    if decision == "contradictory":
        return ["Resolve conflicting physical requirements before design generation"]
    return ["Request a model validated for the stated physics before certification"]

@app.get("/api/intent/examples")
async def list_intent_examples():
    if not INTENT_BENCHMARK.exists():
        raise HTTPException(status_code=503, detail="Recorded intent examples unavailable")
    cases = json.loads(INTENT_BENCHMARK.read_text())["held_out"]
    clarification_examples = []
    if CLARIFICATION_BENCHMARK.exists() and CLARIFICATION_RESULTS.exists():
        clarification_cases = json.loads(CLARIFICATION_BENCHMARK.read_text())["cases"]
        clarification_examples = [{"id": c["id"], "request": c["request"]}
                                  for c in clarification_cases if c["id"] in CLARIFICATION_EXAMPLES]
    return {"examples": [{"id": c["id"], "request": c["request"]} for c in cases if c["id"] in INTENT_EXAMPLES],
            "clarification_examples": clarification_examples,
            "loop_examples": [item for item in clarification_examples if item["id"] in LOOP_EXAMPLES]
                             if CLARIFICATION_LOOPS.exists() else [],
            "local_live_examples": [{"id": "L01", "request": json.loads(LOCAL_LIVE_RECORD.read_text())["request"]}]
                                   if LOCAL_LIVE_RECORD.exists() and LOCAL_LIVE_AUDIT.exists() else [],
            "execution_mode": "RECORDED_MUSE_EXAMPLES"}

@app.post("/api/intent/interpret")
async def interpret_engineering_intent(request: IntentRequest):
    if request.mode == "deterministic":
        try:
            interpretation = compile_intent(request.request_text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"request_text": request.request_text, "interpretation": interpretation,
                "clarification": clarification(interpretation),
                "scientific_plan": intent_plan(interpretation), "physics": None,
                "execution_mode": "LIVE_DETERMINISTIC_INTERPRETATION",
                "notice": "Text interpretation only; no FEA or Muse call executed"}
    if request.mode == "recorded_clarification" and request.example_id in CLARIFICATION_EXAMPLES:
        if not CLARIFICATION_BENCHMARK.exists() or not CLARIFICATION_RESULTS.exists():
            raise HTTPException(status_code=503, detail="Recorded clarification evidence unavailable")
        case = next(c for c in json.loads(CLARIFICATION_BENCHMARK.read_text())["cases"]
                    if c["id"] == request.example_id)
        ledger = json.loads(CLARIFICATION_RESULTS.read_text())
        row = ledger["results"][request.example_id + "/muse_cold"]
        candidate = row["candidate"]
        if candidate is None:
            raise HTTPException(status_code=422, detail="Recorded model output failed schema validation")
        receipt = ledger["receipts"][row["receipt_index"]]
        mapped = {"proceed": "ready_for_static_beam_screen", "clarify": "needs_clarification",
                  "abstain": "unsupported_physics"}
        interpretation = {"decision": mapped[candidate["decision"]],
                          "constraints": candidate["constraints"], "missing": candidate["missing"],
                          "contradictions": [], "unsupported": [],
                          "model_issue_codes": candidate["issue_codes"],
                          "provenance": "recorded_muse_clarification"}
        action = {"action": candidate["decision"], "field": candidate["question_field"],
                  "question": candidate["question"], "reason": "Recorded Muse question from frozen benchmark"}
        return {"example_id": request.example_id, "request_text": case["request"],
                "interpretation": interpretation, "clarification": action,
                "reference_score": row["score"],
                "scientific_plan": (["Ask: " + candidate["question"],
                                     "Do not run FEA until required inputs are known"]
                                    if candidate["decision"] == "clarify" else intent_plan(interpretation)),
                "physics": None, "execution_mode": "RECORDED_MUSE_CLARIFICATION",
                "provenance": {"model": receipt["model"], "request_id": receipt["request_id"],
                               "request_sha256": receipt["request_sha256"],
                               "response_sha256": receipt["response_sha256"],
                               "cost_usd": receipt["estimated_cost_usd"]},
                "notice": "Recorded Muse question; entered answers are compiled live by deterministic rules, without new Muse or FEA calls"}
    if request.mode == "recorded_loop" and request.example_id in LOOP_EXAMPLES:
        if not CLARIFICATION_LOOPS.exists() or not CLARIFICATION_RESULTS.exists():
            raise HTTPException(status_code=503, detail="Recorded clarification loop unavailable")
        record = json.loads(CLARIFICATION_LOOPS.read_text())
        if record.get("status") != "COMPLETE":
            raise HTTPException(status_code=503, detail="Recorded loop is incomplete")
        loop = next(item for item in record["loops"] if item["id"] == request.example_id)
        ledger = json.loads(CLARIFICATION_RESULTS.read_text())
        receipt = ledger["receipts"][loop["muse_receipt_index"]]
        final_trial = next((item for item in loop["trials"] if item["thickness_mm"] == loop["selected"]), None)
        final = final_trial["fine"] if final_trial else None
        task = loop["solver_task"]
        physics = None
        if final:
            physics = {"status": final["status"], "feasible": final["feasible"],
                       "mesh_elements_per_beam": final["mesh_elements_per_beam"],
                       "stroke_mm": final["stroke_mm"], "absolute_drift_mm": final["absolute_drift_mm"],
                       "stress_mpa": final["stress_mpa"], "gates": final["gates"],
                       "constraint_margins": {"stroke_mm": final["stroke_mm"]-task["stroke_min_mm"],
                                              "absolute_drift_mm": task["drift_max_mm"]-final["absolute_drift_mm"],
                                              "stress_mpa": task["stress_max_mpa"]-final["stress_mpa"]},
                       "candidate_source": "deterministic_two_stage_template", "graph": final["proposal"],
                       "envelope_mm": [v*1000 for v in task["envelope_m"]],
                       "physical_scope": "nonlinear_beam_FEA_not_fabrication_validation"}
        return {"example_id": request.example_id, "request_text": loop["original_request"],
                "interpretation": loop["compiled_specification"],
                "scientific_plan": intent_plan(loop["compiled_specification"]),
                "physics": physics, "loop": {"muse_question": loop["muse_question"],
                                             "muse_question_field": loop["muse_question_field"],
                                             "scripted_answer": loop["scripted_answer"],
                                             "solver_assumptions": loop["declared_solver_assumptions"],
                                             "trials": [{"thickness_mm": item["thickness_mm"],
                                                         "coarse_feasible": item["coarse"]["feasible"],
                                                         "coarse_failed_gates": [key for key, passed in item["coarse"].get("gates", {}).items() if not passed],
                                                         "fine_feasible": item["fine"]["feasible"] if item["fine"] else None}
                                                        for item in loop["trials"]],
                                             "selected_thickness_mm": loop["selected"],
                                             "verdict": loop["verdict"]},
                "execution_mode": "RECORDED_MUSE_QUESTION_SCRIPTED_ANSWER_AND_FEA",
                "provenance": {"model": receipt["model"], "request_id": receipt["request_id"],
                               "request_sha256": receipt["request_sha256"],
                               "response_sha256": receipt["response_sha256"],
                               "cost_usd": receipt["estimated_cost_usd"]},
                "notice": "Scripted answer fixture and locally recomputed solver trials; not a live user conversation or hosted FEA"}
    if request.mode == "recorded_local_live" and request.example_id == "L01":
        if not LOCAL_LIVE_RECORD.exists() or not LOCAL_LIVE_AUDIT.exists():
            raise HTTPException(status_code=503, detail="Audited local live record unavailable")
        audit = json.loads(LOCAL_LIVE_AUDIT.read_text())
        if audit.get("status") != "PASS":
            raise HTTPException(status_code=503, detail="Local live audit did not pass")
        record = json.loads(LOCAL_LIVE_RECORD.read_text())
        solver = record["solver"]
        final_trial = next(t for t in solver["trials"] if t["thickness_mm"] == record["robust_repair"]["selected_mm"])
        final = final_trial["fine"]
        task = solver["task"]
        receipt = record["receipts"][0]
        first_failed = next(x for x in solver["joint_corners"] if not x["result"]["feasible"])
        repair_cases = record["robust_repair"]["candidates"][0]["checks"]
        return {"example_id": "L01", "request_text": record["request"],
                "interpretation": record["compiled_specification"],
                "scientific_plan": intent_plan(record["compiled_specification"]),
                "physics": {"status": final["status"], "feasible": final["feasible"],
                            "mesh_elements_per_beam": final["mesh_elements_per_beam"],
                            "stroke_mm": final["stroke_mm"], "absolute_drift_mm": final["absolute_drift_mm"],
                            "stress_mpa": final["stress_mpa"], "gates": final["gates"],
                            "constraint_margins": {"stroke_mm": final["stroke_mm"]-task["stroke_min_mm"],
                                                   "absolute_drift_mm": task["drift_max_mm"]-final["absolute_drift_mm"],
                                                   "stress_mpa": task["stress_max_mpa"]-final["stress_mpa"]},
                            "candidate_source": "deterministic_two_stage_template", "graph": final["proposal"],
                            "envelope_mm": [v*1000 for v in task["envelope_m"]],
                            "physical_scope": "nonlinear_beam_FEA_not_fabrication_validation"},
                "loop": {"muse_question": record["interpretation"]["question"],
                         "muse_question_field": record["interpretation"]["question_field"],
                         "scripted_answer": record["answer"]["text"],
                         "solver_assumptions": solver["assumptions"],
                         "trials": [{"thickness_mm": t["thickness_mm"],
                                     "coarse_feasible": t["coarse"]["feasible"],
                                     "coarse_failed_gates": [key for key, passed in t["coarse"].get("gates", {}).items() if not passed],
                                     "fine_feasible": t["fine"]["feasible"] if t["fine"] else None}
                                    for t in solver["trials"]],
                         "selected_thickness_mm": record["robust_repair"]["selected_mm"],
                         "verdict": record["status"]},
                "initial_joint_failure": {"candidate_thickness_mm": solver["selected_mm"],
                                          "scenario": first_failed["name"],
                                          "absolute_drift_mm": first_failed["result"]["absolute_drift_mm"],
                                          "drift_limit_mm": task["drift_max_mm"]},
                "robust_search": {"candidate_thicknesses_mm": [t["thickness_mm"] for t in solver["trials"]],
                                  "coarse_pass": [t["coarse"]["feasible"] for t in solver["trials"]],
                                  "selected_thickness_mm": record["robust_repair"]["selected_mm"],
                                  "fine_scenarios": [{"name": x["name"], "feasible": x["result"]["feasible"],
                                                      "stroke_mm": x["result"]["stroke_mm"],
                                                      "absolute_drift_mm": x["result"]["absolute_drift_mm"],
                                                      "stress_mpa": x["result"]["stress_mpa"],
                                                      "gates": x["result"]["gates"]} for x in repair_cases],
                                  "fine_robust": True, "scope": "2D beam model and four joint uncertainty corners",
                                  "clearance": "not separately evaluated"},
                "execution_mode": "RECORDED_LOCAL_LIVE_MUSE_AND_FEA",
                "provenance": {"model": receipt["model"], "request_id": receipt["request_id"],
                               "request_sha256": receipt["request_sha256"],
                               "response_sha256": receipt["response_sha256"],
                               "cost_usd": receipt["estimated_cost_usd"]},
                "notice": "Genuine local Muse call and solver run with a scripted answer; hosted app replays audited record"}
    if request.mode != "recorded_muse" or request.example_id not in INTENT_EXAMPLES:
        raise HTTPException(status_code=422, detail="Choose deterministic text interpretation or a listed recorded Muse example")
    if not INTENT_BENCHMARK.exists() or not INTENT_RESULTS.exists():
        raise HTTPException(status_code=503, detail="Recorded Muse evidence unavailable")
    cases = {c["id"]: c for c in json.loads(INTENT_BENCHMARK.read_text())["held_out"]}
    ledger = json.loads(INTENT_RESULTS.read_text())
    case = cases[request.example_id]
    row = ledger["results"][request.example_id + "/muse_cold"]
    receipt = ledger["receipts"][row["receipt_index"]]
    physical = row.get("fine_mesh_physics") or row["physical_screen"].get("physics")
    if physical:
        task = row["physical_screen"]["task"]
        margins = {"stroke_mm": physical["stroke_mm"]-task["stroke_min_mm"],
                   "absolute_drift_mm": task["drift_max_mm"]-physical["absolute_drift_mm"],
                   "stress_mpa": task["stress_max_mpa"]-physical["stress_mpa"]}
        physics = {"status": physical["status"], "feasible": physical["feasible"],
                   "mesh_elements_per_beam": physical["mesh_elements_per_beam"],
                   "stroke_mm": physical["stroke_mm"], "absolute_drift_mm": physical["absolute_drift_mm"],
                   "stress_mpa": physical["stress_mpa"], "gates": physical["gates"],
                   "constraint_margins": margins, "proposal_sha256": physical["proposal_sha256"],
                   "candidate_source": "deterministic_two_stage_template",
                   "graph": physical["proposal"], "envelope_mm": [v*1000 for v in task["envelope_m"]],
                   "physical_scope": "nonlinear_beam_FEA_not_fabrication_validation"}
    else:
        physics = None
    safety_gate = row["physical_screen"]["status"]
    plan = intent_plan(row["candidate"])
    if safety_gate == "blocked_by_independent_safety_gate":
        plan = ["Independent safety gate blocked FEA: " + row["physical_screen"]["reason"],
                "Resolve the physical contradiction before design generation"]
    repair = None
    robustness = None
    robust_search = None
    if request.example_id == "C01" and INTENT_REPAIR.exists():
        record = json.loads(INTENT_REPAIR.read_text())
        final = record["fine_0p9mm"]
        repair = {"method": "deterministic_thickness_sweep", "source": "recorded_numerical_recomputation",
                  "trials": [{"thickness_mm": trial["proposal"]["connections"][0]["thickness"]*1000,
                              "stroke_mm": trial.get("stroke_mm"), "absolute_drift_mm": trial.get("absolute_drift_mm"),
                              "feasible": trial["feasible"]} for trial in record["coarse"]],
                  "final": {"feasible": final["feasible"], "mesh_elements_per_beam": final["mesh_elements_per_beam"],
                            "stroke_mm": final["stroke_mm"], "absolute_drift_mm": final["absolute_drift_mm"],
                            "stress_mpa": final["stress_mpa"], "gates": final["gates"],
                            "proposal_sha256": final["proposal_sha256"], "graph": final["proposal"]},
                  "note": "Thickness sweep changes dimensions within the same graph. It is a deterministic repair, not a new Muse-generated topology."}
        if INTENT_ROBUSTNESS.exists():
            sensitivity = json.loads(INTENT_ROBUSTNESS.read_text())
            robustness = {"mesh_refinement": [{"elements_per_beam": row["elements_per_beam"],
                                               "stroke_mm": row["result"].get("stroke_mm"),
                                               "absolute_drift_mm": row["result"].get("absolute_drift_mm"),
                                               "feasible": row["result"]["feasible"]}
                                              for row in sensitivity["mesh_refinement"]],
                          "parameter_sensitivity": [{"case": row["case"],
                                                      "stroke_mm": row["result"].get("stroke_mm"),
                                                      "absolute_drift_mm": row["result"].get("absolute_drift_mm"),
                                                      "feasible": row["result"]["feasible"]}
                                                     for row in sensitivity["parameter_sensitivity"]],
                          "scope": sensitivity["scope"]}
        if INTENT_ROBUST_SEARCH.exists():
            search = json.loads(INTENT_ROBUST_SEARCH.read_text())
            if search.get("status") == "COMPLETE":
                robust_search = {"candidate_thicknesses_mm": search["predeclared_thicknesses_mm"],
                                 "coarse_pass": [row["all_pass"] for row in search["candidates"]],
                                 "selected_thickness_mm": next((row["thickness_mm"] for row in search["candidates"] if row["all_pass"]), None),
                                 "fine_scenarios": [{"name": row["scenario"], "feasible": row["result"]["feasible"],
                                                     "stroke_mm": row["result"].get("stroke_mm"),
                                                     "absolute_drift_mm": row["result"].get("absolute_drift_mm"),
                                                     "stress_mpa": row["result"].get("stress_mpa"),
                                                     "gates": row["result"].get("gates")}
                                                    for row in search["fine_verification"]],
                                 "fine_robust": search["fine_robust"], "scope": search["scope"],
                                 "clearance": "not separately evaluated"}
    return {"example_id": request.example_id, "request_text": case["request"],
            "interpretation": row["candidate"], "reference_score": row["score"],
            "scientific_plan": plan, "physics": physics, "repair": repair, "robustness": robustness,
            "robust_search": robust_search,
            "safety_gate": safety_gate,
            "execution_mode": "RECORDED_MUSE_INTERPRETATION_AND_PHYSICS_REPLAY",
            "provenance": {"model": receipt["model"], "request_id": receipt["request_id"],
                           "request_sha256": receipt["request_sha256"], "response_sha256": receipt["response_sha256"],
                           "cost_usd": receipt["cost_usd"]},
            "notice": "Stored model interpretation and locally recomputed FEA; no live model or solver call executed"}

def load_ledger():
    global RUNS_STATE
    if RUNS_DB_FILE.exists():
        try:
            with open(RUNS_DB_FILE, "r") as f:
                RUNS_STATE = json.load(f)
        except Exception:
            RUNS_STATE = {}

def save_ledger():
    try:
        with open(RUNS_DB_FILE, "w") as f:
            json.dump(RUNS_STATE, f, indent=2)
    except Exception as e:
        print(f"Error saving ledger: {e}")

load_ledger()

async def emit_event(run_id: str, step: str, title: str, details: Dict[str, Any], status: str = "in_progress"):
    event_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "step": step,
        "title": title,
        "status": status,
        "details": details
    }
    if run_id in RUNS_STATE:
        RUNS_STATE[run_id]["timeline"].append(event_payload)
        RUNS_STATE[run_id]["last_updated"] = event_payload["timestamp"]
        RUNS_STATE[run_id]["status"] = status
        save_ledger()

    if run_id in RUN_EVENT_QUEUES:
        await RUN_EVENT_QUEUES[run_id].put(event_payload)

async def execute_design_job(run_id: str, request: DesignRequest):
    try:
        await emit_event(
            run_id,
            step="INITIALIZATION",
            title="Design Objective Initialized",
            details={
                "target_stroke_mm": request.stroke_target_mm,
                "applied_load_N": request.load_fy_n,
                "yield_stress_limit_MPa": request.max_stress_mpa,
                "execution_mode": request.mode,
                "material": "Polypropylene (E=1.4 GPa, Yield=35 MPa, nu=0.42)",
                "envelope_mm": [90.0, 55.0, 10.0]
            }
        )
        await asyncio.sleep(0.6)

        spec = None
        raw_receipt = {}

        if request.mode == "replay_hero":
            receipt_path = ENGINEERING_DIR / "muse_exp01_a_feasible_fixture.json"
            with open(receipt_path) as f:
                spec = json.load(f)
            raw_receipt = {
                "source": "Meta Muse Discovery Campaign (exp_01_A)",
                "model": "muse-spark-1.3",
                "evidence_status": "STORED_FIXTURE; ORIGINAL_REQUEST_NOT_ATTACHED"
            }
        elif request.mode == "replay_p0":
            receipt_path = ENGINEERING_DIR / "p0_double_folded_fixture.json"
            with open(receipt_path) as f:
                spec = json.load(f)
            raw_receipt = {
                "source": "Deterministic P0 Double-Folded Baseline",
                "model": "classical_synthesis",
                "evidence_status": "DETERMINISTIC_FIXTURE"
            }
        elif request.mode == "replay_call3":
            receipt_path = ENGINEERING_DIR / "blinded_call3_receipt.json"
            with open(receipt_path) as f:
                data = json.load(f)
            spec = data.get("fixture", data)
            raw_receipt = {
                "source": "Meta Muse Zero-Shot Blinded Proposal (Call 3)",
                "model": "muse-spark-1.3",
                "evidence_status": "STORED_FIXTURE; ORIGINAL_REQUEST_NOT_ATTACHED"
            }
        elif request.mode == "dry_run":
            receipt_path = ENGINEERING_DIR / "muse_exp01_a_feasible_fixture.json"
            with open(receipt_path) as f:
                spec = json.load(f)
            raw_receipt = {"source": "Local fixture", "execution_mode": "DRY_RUN", "spend_usd": 0.0}
        else:
            raise ValueError(f"Unsupported execution mode: {request.mode}")

        raw_receipt["execution_mode"] = "REPLAY" if request.mode.startswith("replay_") else "DRY_RUN"
        raw_receipt["new_api_spend_usd"] = 0.0

        await emit_event(
            run_id,
            step="MUSE_GENERATION",
            title="Stored Topology Loaded",
            details={
                "topology_name": spec.get("topology_name", "Unknown"),
                "design_rationale": spec.get("design_rationale", "Bilateral symmetrical flexure guide"),
                "provenance": raw_receipt,
                "anchors_count": len(spec.get("anchors", [])),
                "stages_count": len(spec.get("stages", [])),
                "connections_count": len(spec.get("connections", []))
            }
        )
        await asyncio.sleep(0.7)

        # 2. Geometry Compilation & Manifold Checking
        compiler = HardenedCompactCompiler()
        try:
            mesh_coarse = compiler.compile(spec, n_elem_per_beam=12)
            nodes = np.array(mesh_coarse["nodes"])
            elements = mesh_coarse["elements"]
            widths = mesh_coarse["widths"]
            act_node = mesh_coarse["output_node"]
            ground_nodes = mesh_coarse["ground_nodes"]

            await emit_event(
                run_id,
                step="GEOMETRY_COMPILATION",
                title="Deterministic Geometry Compiler: PASSED",
                details={
                    "status": "PASS",
                    "nodes_count": len(nodes),
                    "elements_count": len(elements),
                    "ground_nodes": ground_nodes,
                    "actuation_output_node": act_node,
                    "envelope_compliant": True,
                    "min_thickness_mm": float(min(widths) * 1000.0)
                }
            )
        except Exception as e:
            await emit_event(
                run_id,
                step="GEOMETRY_COMPILATION",
                title="Deterministic Geometry Compiler: REJECTED",
                details={"status": "FAIL", "reason": str(e)},
                status="rejected"
            )
            return

        await asyncio.sleep(0.7)

        # 3. Coarse-Mesh Nonlinear FEA (N=12/beam)
        solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)
        num_nodes = len(nodes)
        total_dof = 3 * num_nodes
        boundary_dofs = []
        for g in ground_nodes:
            boundary_dofs.extend([3*g, 3*g+1, 3*g+2])

        f_ext = np.zeros(total_dof)
        f_ext[3*act_node + 1] = float(request.load_fy_n)

        try:
            sol_coarse = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundary_dofs, f_ext)
            u_c = sol_coarse["displacements"]
            dy_c = float(u_c[3*act_node + 1] * 1000.0)
            dx_c = float(abs(u_c[3*act_node]) * 1000.0)
            sig_c = float(sol_coarse["max_stress_MPa"])

            await emit_event(
                run_id,
                step="COARSE_NONLINEAR_FEA",
                title="Coarse Nonlinear FEA (N=12/beam) Evaluated",
                details={
                    "stroke_dy_mm": round(dy_c, 4),
                    "peak_stress_MPa": round(sig_c, 2),
                    "parasitic_dx_mm": round(dx_c, 6),
                    "solver_increments": len(sol_coarse["step_history"]),
                    "converged": True,
                    "safety_factor": round(sol_coarse["safety_factor"], 2)
                }
            )
        except Exception as e:
            await emit_event(
                run_id,
                step="COARSE_NONLINEAR_FEA",
                title="Coarse Nonlinear FEA Diverged",
                details={"error": str(e)},
                status="diverged"
            )
            return

        await asyncio.sleep(0.7)

        # 4. Record frozen sizing inputs; this workflow does not run an optimizer.
        await emit_event(
            run_id,
            step="SIZING_INPUTS",
            title="Stored Geometry Sizing Loaded",
            details={
                "source": "stored_fixture",
                "optimizer_executed": False,
                "minimum_element_width_mm": float(np.min(widths) * 1000.0),
                "target_stroke_mm": request.stroke_target_mm,
            }
        )
        await asyncio.sleep(0.7)

        # 5. Fine-Mesh Verification (N=48/beam) + Tangent Eigenvalue Audit
        mesh_fine = compiler.compile(spec, n_elem_per_beam=48)
        nodes_f = np.array(mesh_fine["nodes"])
        elements_f = mesh_fine["elements"]
        widths_f = mesh_fine["widths"]
        act_f = mesh_fine["output_node"]
        num_nodes_f = len(nodes_f)
        total_dof_f = 3 * num_nodes_f

        boundary_dofs_f = []
        for g in mesh_fine["ground_nodes"]:
            boundary_dofs_f.extend([3*g, 3*g+1, 3*g+2])

        f_ext_f = np.zeros(total_dof_f)
        f_ext_f[3*act_f + 1] = float(request.load_fy_n)

        sol_fine = solver.solve_nonlinear_newton_raphson(nodes_f, elements_f, widths_f, boundary_dofs_f, f_ext_f)
        u_f = sol_fine["displacements"]
        dy_f = float(u_f[3*act_f + 1] * 1000.0)
        dx_f = float(abs(u_f[3*act_f]) * 1000.0)
        sig_f = float(sol_fine["max_stress_MPa"])

        # Tangent stiffness stability audit
        f_int, K_tan, _ = solver.compute_internal_forces_and_tangent(nodes_f, elements_f, widths_f, u_f)
        free_dofs_f = [i for i in range(total_dof_f) if i not in boundary_dofs_f]
        K_red = K_tan[np.ix_(free_dofs_f, free_dofs_f)]
        eigs = np.linalg.eigvalsh(K_red)
        min_eig = float(np.min(eigs))

        is_stable = bool(min_eig > 0)
        is_stroke_ok = bool(dy_f >= request.stroke_target_mm)
        is_stress_ok = bool(sig_f <= request.max_stress_mpa)
        is_parasitic_ok = bool(dx_f <= 0.200000)
        is_strictly_feasible = is_stable and is_stroke_ok and is_stress_ok and is_parasitic_ok

        await emit_event(
            run_id,
            step="FINE_MESH_AUDIT",
            title=f"Fine-Mesh (N=48) Verification: {'STRICT PASS' if is_strictly_feasible else 'INCOMPLETE'}",
            details={
                "mesh_elements": len(elements_f),
                "mesh_nodes": len(nodes_f),
                "stroke_dy_mm": round(dy_f, 4),
                "target_stroke_mm": request.stroke_target_mm,
                "stroke_margin_um": round((dy_f - request.stroke_target_mm) * 1000.0, 1),
                "peak_stress_MPa": round(sig_f, 2),
                "parasitic_dx_mm": round(dx_f, 6),
                "min_tangent_eigenvalue_N_per_m": min_eig,
                "tangent_stability": "STABLE (All λ > 0)" if is_stable else "UNSTABLE BIFURCATION (λ ≤ 0)",
                "strict_feasible": is_strictly_feasible
            }
        )
        await asyncio.sleep(0.7)

        # 6. Synthesize 3D Solid Model with Turbo Colormap FEA Stress Field
        renderer = FEASolidRenderer(depth=0.010, max_stress_scale=25.0)
        mesh_3d, metrics_3d = renderer.generate_fea_solid(spec, n_elem_per_beam=16, load_n=request.load_fy_n)
        glb_filename = f"run_{run_id}.glb"
        out_glb_path = ARTIFACT_DIR / glb_filename
        mesh_3d.export(str(out_glb_path))

        await emit_event(
            run_id,
            step="GLB_GENERATION",
            title="3D Solid FEA Manifold Exported",
            details={
                "glb_url": f"/backend/artifacts/{glb_filename}",
                "bounds_mm": np.round(mesh_3d.bounds * 1000.0, 2).tolist(),
                "mesh_triangles": len(mesh_3d.faces),
                "stress_field_colors": "ANSYS/COMSOL Turbo Gradient (0 to 25 MPa)"
            }
        )
        await asyncio.sleep(0.5)

        # 7. Final Verdict
        final_status = "PASS" if is_strictly_feasible else "FAIL"
        RUNS_STATE[run_id]["result"] = {
            "verdict": final_status,
            "stroke_dy_mm": dy_f,
            "peak_stress_MPa": sig_f,
            "parasitic_dx_mm": dx_f,
            "min_tangent_eigenvalue": min_eig,
            "glb_url": f"/backend/artifacts/{glb_filename}",
            "spec": spec,
            "provenance": raw_receipt
        }
        await emit_event(
            run_id,
            step="COMPLETION",
            title=f"Autonomous Engineering Run Completed: {final_status}",
            details=RUNS_STATE[run_id]["result"],
            status="completed" if is_strictly_feasible else "failed"
        )

    except Exception as exc:
        import traceback
        err = traceback.format_exc()
        await emit_event(
            run_id,
            step="SYSTEM_ERROR",
            title="Engineering Workflow Exception",
            details={"error": str(exc), "traceback": err},
            status="error"
        )

@app.post("/api/workflow/run")
async def start_design_workflow(request: DesignRequest, background_tasks: BackgroundTasks):
    if request.mode not in {"replay_hero", "replay_p0", "replay_call3", "dry_run"}:
        raise HTTPException(status_code=422, detail="Unsupported execution mode; live Muse is not implemented")
    if HOSTED_DEMO and request.mode != "replay_hero":
        raise HTTPException(status_code=422, detail="Hosted demo serves the verified hero replay only")
    if HOSTED_DEMO and (request.stroke_target_mm != 3.0 or request.load_fy_n != 5.0 or request.max_stress_mpa != 25.0):
        raise HTTPException(status_code=422, detail="Hosted verified replay is fixed at 3 mm, 5 N, and 25 MPa")
    run_id = str(uuid.uuid4())[:8]
    if HOSTED_DEMO:
        template = json.loads((ENGINEERING_DIR / "verified_hero_replay.json").read_text())
        result = copy.deepcopy(template["result"])
        result["glb_url"] = "/backend/artifacts/verified_hero_replay.glb"
        timeline = copy.deepcopy(template["timeline"])
        for event in timeline:
            event["run_id"] = run_id
            if event.get("step") == "MUSE_GENERATION":
                event["title"] = "Stored Muse Topology Replayed"
                event["details"]["provenance"] = result["provenance"]
            elif event.get("step") == "COMPLETION":
                event["details"] = result
            elif event.get("step") == "SCIPY_OPTIMIZATION":
                event["step"] = "SIZING_INPUTS"
                event["title"] = "Stored Geometry Sizing Loaded"
                event["details"] = {"source": "stored_fixture", "optimizer_executed": False}
            elif event.get("step") == "GLB_GENERATION":
                event["details"]["glb_url"] = result["glb_url"]
        RUNS_STATE[run_id] = {
            "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
            "request": request.model_dump(), "timeline": timeline, "status": "completed",
            "result": result, "execution_mode": "HOSTED_VERIFIED_REPLAY",
        }
        save_ledger()
        return {"run_id": run_id, "status": "completed", "message": "Verified local run replayed; no solver or API call executed"}
    RUNS_STATE[run_id] = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": request.model_dump(),
        "timeline": [],
        "status": "queued"
    }
    RUN_EVENT_QUEUES[run_id] = asyncio.Queue()
    save_ledger()

    background_tasks.add_task(execute_design_job, run_id, request)
    return {"run_id": run_id, "status": "queued", "message": "Engineering workflow spawned"}

@app.get("/api/workflow/{run_id}/stream")
async def stream_workflow_events(run_id: str):
    if run_id not in RUNS_STATE:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        # Replay past events in timeline first
        if run_id in RUNS_STATE:
            for ev in RUNS_STATE[run_id]["timeline"]:
                yield f"data: {json.dumps(ev)}\n\n"

        # Stream new events from the queue
        q = RUN_EVENT_QUEUES.get(run_id)
        if q:
            while True:
                ev = await q.get()
                yield f"data: {json.dumps(ev)}\n\n"
                if ev.get("status") in ["completed", "failed", "rejected", "diverged", "error"]:
                    break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/runs")
async def list_runs():
    return {"runs": list(RUNS_STATE.values())}

@app.get("/api/runs/{run_id}")
async def get_run_details(run_id: str):
    if run_id not in RUNS_STATE:
        raise HTTPException(status_code=404, detail="Run not found")
    return RUNS_STATE[run_id]

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Neodustria Autonomous Engineering Orchestrator",
        "version": "2.0.0",
        "time": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/scientific-memory")
async def get_scientific_memory():
    laws_path = Path("corrected_phase8_1_dimensionless_laws.json")
    laws = {}
    if laws_path.exists():
        with open(laws_path) as f:
            laws = json.load(f)
    closed_loop_path = Path("autonomous_discovery_closed_loop_receipt.json")
    discovery = {}
    if closed_loop_path.exists():
        with open(closed_loop_path) as f:
            discovery = json.load(f)
    transfer_path = Path("scientific_memory_transfer_verification.json")
    transfer = {}
    if transfer_path.exists():
        with open(transfer_path) as f:
            transfer = json.load(f)
    archive_path = Path("map_elites_pareto_archive.json")
    archive = {}
    if archive_path.exists():
        with open(archive_path) as f:
            archive = json.load(f)
    gen_results_path = Path("rigorous_12config_generalization_results.json")
    gen_results = {}
    if gen_results_path.exists():
        with open(gen_results_path) as f:
            gen_results = json.load(f)
    return {
        "dimensionless_laws": laws,
        "autonomous_discovery_episode": discovery,
        "scientific_memory_transfer": transfer,
        "map_elites_archive": archive,
        "generalization_12config": gen_results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

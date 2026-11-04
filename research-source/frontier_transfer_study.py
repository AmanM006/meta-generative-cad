"""Frozen three-task transfer pilot; records raw model receipts and all FEA trials.

Run only after fresh_evidence/frontier_transfer_tasks_frozen.json exists. The
module never edits task specifications. It resumes from its output ledger.
"""
import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from fresh_matched_benchmark import meta_key
from frontier_novel_graph_challenge import deterministic_graph
from open_ended_structural_discovery_engine import digest, evaluate

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/frontier_transfer_tasks_frozen.json"
OUT = ROOT / "fresh_evidence/frontier_transfer_study.json"
PRIOR = ROOT / "fresh_evidence/frontier_novel_graph_challenge.json"
MAX_NEW_COST_USD = 0.10


def save(state):
    OUT.write_text(json.dumps(state, indent=2))


def model_call(prompt, state):
    key = meta_key()
    if not key:
        raise RuntimeError("MODEL_API_KEY unavailable")
    spent = sum(x.get("cost_usd", 0) for x in state["receipts"])
    if spent > MAX_NEW_COST_USD - 0.01:
        raise RuntimeError("Local pilot budget reached")
    request = {"model": "muse-spark-1.3", "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.3, "reasoning_effort": "minimal", "max_completion_tokens": 4500}
    started = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=key, timeout=60).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    receipt = {"request_id": response.id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "request": request, "response": raw, "request_sha256": digest(request),
               "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
               "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
               "cost_usd": (usage.prompt_tokens*0.20+usage.completion_tokens*0.80)/1e6,
               "latency_s": time.perf_counter()-started, "finish_reason": response.choices[0].finish_reason}
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        receipt["parsing_status"] = "parsed" if isinstance(parsed, dict) else "not_object"
    except ValueError:
        parsed = None
        receipt["parsing_status"] = "parse_failed"
    state["receipts"].append(receipt)
    save(state)
    return parsed, len(state["receipts"])-1


def discovery_graph(prior, experiment):
    proposal = copy.deepcopy(prior["muse"][2]["proposal"])
    if experiment == "extend_anchors_to_edges":
        for a in proposal["anchors"]:
            a[0] = 0.0 if a[0] < 0.045 else 0.09
    elif experiment == "increase_thickness_to_0p75mm":
        for e in proposal["connections"]:
            e["thickness"] = 0.00075
    elif experiment == "increase_stage_height_20pct":
        for stage in proposal["stages"]:
            stage["height"] *= 1.2
            stage.pop("height_m", None)
    else:
        raise ValueError("Unknown discovery experiment")
    return proposal


def classical_candidates(task):
    sx, sy = task["envelope_m"]
    # Frozen physics-informed sweep: longer and shorter bending spans, both at
    # the manufacturing thickness floor. Two FEA calls, as in each Muse arm.
    proposals = [deterministic_graph(0.34*sx, 0.66*sx, 0.44*sy, 0.0006),
                 deterministic_graph(0.30*sx, 0.70*sx, 0.36*sy, 0.0006)]
    for proposal in proposals:
        for anchor in proposal["anchors"]:
            anchor[0] = 0.0 if anchor[0] == 0.0 else sx
            anchor[1] += sy/2 - 0.0275
        for stage in proposal["stages"]:
            stage["center"][1] = sy/2
    return proposals


def prompt_for(task, condition, history, principle):
    preface = (
        "Propose exactly TWO valid two-stage compliant mechanism graphs for this NEW task: "
        + json.dumps(task) + ". Return JSON {\"proposals\":[graph,graph],\"reasoning\":string}. "
        "Every graph has anchors [x_m,y_m], exactly two stages {type:rigid_stage,center:[x,y],height:m}, "
        "2-16 connections {type:flexure_beam,from_type,from_index,from_port,to_type,to_index,to_port,thickness}, "
        "and output_stage. Stage ports top/bot/center; anchor port center. "
        "Minimum flexure thickness 0.0006m, no crossed beams, all coordinates within envelope. "
        "All proposals are evaluated without repair. Use bending load paths, absolute drift and stress constraints. "
    )
    if condition == "muse_raw_history":
        preface += "Prior raw observations (not a validated law): " + json.dumps(history)
    elif condition == "muse_validated_principle":
        preface += "Previously tested scientific principle with caveat: " + json.dumps(principle)
    return preface


def main():
    frozen = json.loads(FROZEN.read_text())
    check = {k: v for k, v in frozen.items() if k != "frozen_spec_sha256"}
    if digest(check) != frozen["frozen_spec_sha256"]:
        raise RuntimeError("Frozen benchmark checksum mismatch")
    prior = json.loads(PRIOR.read_text())
    state = json.loads(OUT.read_text()) if OUT.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_spec_sha256": frozen["frozen_spec_sha256"],
        "source_prior_sha256": digest(prior), "receipts": [], "discovery": {}, "transfer": {}}
    if state["frozen_spec_sha256"] != frozen["frozen_spec_sha256"]:
        raise RuntimeError("Output ledger uses different benchmark")
    save(state)
    discovery = state["discovery"]
    if "initial_model" not in discovery:
        failure = {k: prior["muse"][2].get(k) for k in ("stroke_mm", "absolute_drift_mm", "stress_mpa", "gates")}
        prompt = ("A two-stage 90x55mm polypropylene graph under 4N failed stroke>=2.2mm: "
                  + json.dumps(failure) + ". Its beams are already at the 0.6mm floor. "
                  "Form a falsifiable mechanical hypothesis. Choose ONE discriminating FEA experiment from: "
                  "extend_anchors_to_edges, increase_thickness_to_0p75mm, increase_stage_height_20pct. "
                  "Return JSON {hypothesis:string, experiment:string, expected_stroke_direction:string}.")
        parsed, index = model_call(prompt, state)
        discovery["initial_model"] = parsed
        discovery["initial_receipt_index"] = index
        save(state)
    choice = (discovery["initial_model"] or {}).get("experiment")
    if choice not in ("extend_anchors_to_edges", "increase_thickness_to_0p75mm", "increase_stage_height_20pct"):
        discovery["invalid_experiment_choice"] = choice
        choice = "increase_stage_height_20pct"  # predeclared fallback; counts as model failure
    if "experiment_result" not in discovery:
        candidate = discovery_graph(prior, choice)
        discovery["experiment_result"] = evaluate(candidate, prior["task"])
        discovery["experiment_choice_executed"] = choice
        save(state)
    if "revised_model" not in discovery:
        prompt = ("Your hypothesis and chosen experiment: " + json.dumps(discovery["initial_model"])
                  + ". Actual nonlinear FEA result: " + json.dumps({k: discovery["experiment_result"].get(k)
                     for k in ("status", "stroke_mm", "absolute_drift_mm", "stress_mpa", "gates", "reason")})
                  + ". Revise or reject the hypothesis. Return JSON {principle:string,caveat:string,"
                  "supported_by_this_experiment:boolean, counterexample:string}.")
        parsed, index = model_call(prompt, state)
        discovery["revised_model"] = parsed
        discovery["revision_receipt_index"] = index
        save(state)
    history = {"before": {k: prior["muse"][2].get(k) for k in ("stroke_mm", "absolute_drift_mm", "stress_mpa", "gates")},
               "experiment": choice,
               "after": {k: discovery["experiment_result"].get(k) for k in ("stroke_mm", "absolute_drift_mm", "stress_mpa", "gates")}}
    principle = discovery["revised_model"]
    for task in frozen["tasks"]:
        for arm in frozen["arms"]:
            key = task["id"] + "/" + arm
            if key in state["transfer"]:
                continue
            if arm == "deterministic_physics":
                proposals = classical_candidates(task)
                receipt_index = None
            else:
                parsed, receipt_index = model_call(prompt_for(task, arm, history, principle), state)
                proposals = (parsed or {}).get("proposals", []) if isinstance(parsed, dict) else []
            rows = []
            for candidate in proposals[:2]:
                if not isinstance(candidate, dict) or len(candidate.get("stages", [])) != 2:
                    rows.append({"proposal": candidate, "status": "rejected", "feasible": False,
                                 "reason": "Invalid graph or wrong stage count"})
                else:
                    rows.append(evaluate(candidate, task))
            while len(rows) < 2:
                rows.append({"status": "missing_proposal", "feasible": False})
            state["transfer"][key] = {"receipt_index": receipt_index, "coarse": rows}
            save(state)
            print(key, [r.get("feasible") for r in rows], flush=True)
    for task in frozen["tasks"]:
        for arm in frozen["arms"]:
            key = task["id"] + "/" + arm
            row = state["transfer"][key]
            if "fine_best" in row:
                continue
            candidates = [r for r in row["coarse"] if r.get("status") == "evaluated"]
            if candidates:
                best = max(candidates, key=lambda r: r.get("stroke_mm", float("-inf")))
                row["fine_best"] = evaluate(best["proposal"], task, mesh_density=48)
            else:
                row["fine_best"] = {"status": "no_valid_candidate", "feasible": False}
            save(state)
            print("FINE", key, row["fine_best"]["feasible"], flush=True)
    state["status"] = "COMPLETE"
    state["new_model_cost_usd"] = sum(r["cost_usd"] for r in state["receipts"])
    save(state)
    print("COMPLETE cost_usd", state["new_model_cost_usd"])


if __name__ == "__main__":
    main()

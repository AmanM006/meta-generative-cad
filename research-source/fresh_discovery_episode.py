"""Fresh blinded Muse hypothesis revision with actual FEA and a fitted control."""
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openai import OpenAI
from scipy.optimize import least_squares

from fresh_matched_benchmark import ROOT, OUT, meta_key, sha
from neodustria_gp_first_scientist import compile_arch
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

path = OUT / "fresh_discovery_episode.json"
eng = TopologyInnovationEngineV2(env_x=0.060, env_y=0.040, material_E=1.4e9)
cge = CompositionalGraphEngine(0.060, 0.040)
_, spec = compile_arch(eng, cge, ("compositional", "folded_floating_shuttle", 0), 1.0)
grid = [(f, h) for f in (0.7, 1.4, 2.8, 3.5) for h in (800, 950, 1100)]
initial_training = [(0.7, 800), (2.8, 1100), (1.4, 950)]
experiment_choices = [(0.7, 1100), (1.4, 800), (2.8, 950), (3.5, 800)]
holdout = [x for x in grid if x not in initial_training and x not in experiment_choices]

def observation(point):
    f, h = point
    t0 = time.perf_counter()
    result = eng.evaluate_task_specific(spec, h*1e-6, f, 0.1, 30.0, max_drift_mm=0.5)
    return {"force_N": f, "thickness_um": h, "result": result,
            "duration_s": time.perf_counter()-t0}

def call(messages, association):
    request = {"model": "muse-spark-1.3", "messages": messages, "temperature": 0.2,
               "reasoning_effort": "minimal", "max_completion_tokens": 1500}
    t0 = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=meta_key(), timeout=30).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    cost = (usage.prompt_tokens*0.20 + usage.completion_tokens*0.80)/1e6
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        status = "parsed"
    except ValueError:
        parsed, status = None, "parse_failed"
    return parsed, {"association": association, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "request_id": response.id, "request": request, "response": raw,
                    "request_sha256": sha(request), "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
                    "cost_usd": cost, "latency_s": time.perf_counter()-t0,
                    "finish_reason": response.choices[0].finish_reason, "parsing_status": status}

def params(parsed):
    try:
        p = [float(parsed[k]) for k in ("C", "alpha", "beta")]
        return p if all(math.isfinite(x) for x in p) and p[0] > 0 else None
    except (TypeError, ValueError, KeyError):
        return None

def predict(p, row):
    return p[0] * row["force_N"]**p[1] * (row["thickness_um"]/1000)**p[2]

def rmse(p, rows):
    return float(np.sqrt(np.mean([(predict(p, x)-x["result"]["stroke_dy_mm"])**2 for x in rows])))

def main():
    ledger = json.loads((ROOT/"PHASE23_5_AUTHENTIC_MUSE_REQUEST_LEDGER.json").read_text())
    if ledger["total_cost_usd"] >= 49.75 or not meta_key():
        raise RuntimeError("Missing credential or insufficient authorized budget")
    evidence = {"created_utc": datetime.now(timezone.utc).isoformat(), "geometry_spec": spec,
                "geometry_sha256": sha(spec), "initial_training": [observation(x) for x in initial_training],
                "experiment_choices": experiment_choices, "holdout_points": holdout}
    path.write_text(json.dumps(evidence, indent=2, default=str))
    prompt = ("A compliant folded shuttle is evaluated by nonlinear FEA. Predict stroke_mm = C * "
              "force_N^alpha * (thickness_um/1000)^beta. Give C, alpha, beta as numbers and choose "
              "one experiment from the listed choices to most strongly test your law. Return only JSON "
              "with C, alpha, beta, experiment_index (zero based), rationale. "
              "Training observations: " + json.dumps(evidence["initial_training"], default=str)
              + " Choices: " + json.dumps(experiment_choices))
    first, receipt1 = call([{"role": "user", "content": prompt}], "initial_hypothesis")
    evidence["initial_hypothesis"], evidence["initial_receipt"] = first, receipt1
    index = int(first["experiment_index"]) if first and isinstance(first.get("experiment_index"), int) else -1
    if index not in range(len(experiment_choices)):
        evidence["status"] = "INVALID_EXPERIMENT_SELECTION"
        path.write_text(json.dumps(evidence, indent=2, default=str))
        return
    evidence["chosen_experiment"] = observation(experiment_choices[index])
    path.write_text(json.dumps(evidence, indent=2, default=str))
    revision_prompt = ("Your frozen hypothesis was " + json.dumps(first) + ". New nonlinear FEA result: "
                       + json.dumps(evidence["chosen_experiment"], default=str)
                       + ". Revise C, alpha, beta for stroke_mm = C * force_N^alpha * "
                       "(thickness_um/1000)^beta. Return JSON with C, alpha, beta, rationale only.")
    revised, receipt2 = call([{"role": "user", "content": revision_prompt}], "revised_hypothesis")
    evidence["revised_hypothesis"], evidence["revision_receipt"] = revised, receipt2
    evidence["untouched_holdout"] = [observation(x) for x in holdout]
    training = evidence["initial_training"] + [evidence["chosen_experiment"]]
    fitted = least_squares(lambda p: [predict(p, x)-x["result"]["stroke_dy_mm"] for x in training],
                           x0=[1.0, 1.0, -2.0], bounds=([0, -5, -5], [100, 5, 5])).x.tolist()
    p0, p1 = params(first), params(revised)
    evidence["scores"] = {"initial_rmse_mm": rmse(p0, evidence["untouched_holdout"]) if p0 else None,
                          "revised_rmse_mm": rmse(p1, evidence["untouched_holdout"]) if p1 else None,
                          "classical_nonlinear_least_squares_rmse_mm": rmse(fitted, evidence["untouched_holdout"]),
                          "classical_fit_parameters": fitted}
    evidence["fresh_api_cost_usd"] = receipt1["cost_usd"] + receipt2["cost_usd"]
    evidence["status"] = "COMPLETE"
    path.write_text(json.dumps(evidence, indent=2, default=str))
    print(evidence["scores"], "cost", evidence["fresh_api_cost_usd"])

if __name__ == "__main__":
    main()

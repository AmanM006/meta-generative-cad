"""Fresh paired Muse vs deterministic rescue with complete local FEA traces."""
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI
from neodustria_gp_first_scientist import (
    CASM_PRIOR_ORDER, KAPPA_TABLE_CALIBRATED, NeodustriaGPFirstScientist,
    check_strict_acceptance, compile_arch,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "fresh_evidence"
OUT.mkdir(exist_ok=True)
MAX_COST = 0.25  # Additional hard ceiling, below the user's $50 cumulative limit.
spent = 0.0

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)

def sha(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

def save(obj):
    path = OUT / "matched_benchmark.json"
    temp = OUT / f"matched_benchmark_{uuid.uuid4().hex}.tmp"
    temp.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    for attempt in range(5):
        try:
            temp.replace(path)
            return
        except PermissionError:
            time.sleep(0.1 * (attempt + 1))
    # Windows readers can hold the destination open; keep the complete checkpoint.
    raise RuntimeError(f"Could not replace {path}; checkpoint retained at {temp}")

def meta_key():
    p = ROOT / "horizonforge-local-test" / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("MODEL_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("MODEL_API_KEY")

def muse_sweep(task):
    global spent
    historical = json.loads((ROOT / "PHASE23_5_AUTHENTIC_MUSE_REQUEST_LEDGER.json").read_text())["total_cost_usd"]
    if spent >= MAX_COST or historical + spent >= 50 or not meta_key():
        raise RuntimeError("Meta key unavailable or fresh spending cap reached")
    prompt = ("Choose four blade thicknesses in micrometers between 750 and 1000 for a "
              "folded floating shuttle. Return JSON with recommended_thicknesses_um and rationale. "
              "You have no FEA outcomes for this task. Task: " + canonical(task))
    request = {"model": "muse-spark-1.3", "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.2, "max_completion_tokens": 1500, "reasoning_effort": "minimal"}
    t0 = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=meta_key(), timeout=20).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    cost = ((usage.prompt_tokens * 0.20 + usage.completion_tokens * 0.80) / 1e6) if usage else None
    if cost is not None:
        spent += cost
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        values = parsed["recommended_thicknesses_um"]
        sweep = [float(v) for v in values[:4] if 750 <= float(v) <= 1000]
        status = "parsed" if sweep else "invalid_values"
    except (ValueError, KeyError, TypeError):
        sweep, status = [], "parse_failed"
    receipt = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "request_id": response.id,
               "model": response.model, "request": request, "response": raw,
               "finish_reason": response.choices[0].finish_reason,
               "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
               "request_sha256": sha(request), "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
               "prompt_tokens": usage.prompt_tokens if usage else None,
               "completion_tokens": usage.completion_tokens if usage else None,
               "cost_usd": cost, "latency_s": time.perf_counter()-t0, "parsing_status": status}
    return sweep, receipt

def trial(task, arm, prefix):
    agent = NeodustriaGPFirstScientist(task, seed=42, max_budget=20)
    rows = []
    started = time.perf_counter()
    def evaluate(arch, thickness, source):
        t0 = time.perf_counter()
        row = {"index": len(rows)+1, "source": source, "architecture": arch,
               "thickness_m": thickness, "taper_ratio": 1.0, "force_N": task["Fy_N"]}
        try:
            _, spec = compile_arch(agent.eng, agent.cge, arch, 1.0)
            row["geometry_spec"] = spec
            result = agent.eng.evaluate_task_specific(spec, thickness, agent.Fy, agent.req_dy,
                                                       agent.max_sig, max_drift_mm=agent.max_dx)
            good, reason = check_strict_acceptance(result, task)
            row.update(result=result, feasible=bool(good), reason=reason)
        except Exception as exc:
            row.update(feasible=False, reason=f"EXCEPTION:{type(exc).__name__}:{exc}")
        row["duration_s"] = time.perf_counter()-t0
        rows.append(row)
        save({**prefix, "current_arm": arm, "current_task": task["task_id"], "partial_rows": rows})
        return row["feasible"]
    for arch in CASM_PRIOR_ORDER:
        kappa = KAPPA_TABLE_CALIBRATED.get(arch[1], 0.018)
        h = (kappa*agent.Fy*agent.env_x**3/(agent.mat_E*agent.b*agent.req_dy*1e-3))**(1/3)
        if evaluate(arch, max(agent.th_min, min(agent.th_max, h)), "shared_CASM_GP_prior"):
            break
    receipt = None
    if not any(r["feasible"] for r in rows):
        if arm == "muse":
            try:
                sweep, receipt = muse_sweep(task)
            except Exception as exc:
                sweep = []
                receipt = {"error": f"{type(exc).__name__}: {exc}", "status": "no_inference"}
        else:
            sweep = [800, 850, 900, 950]
        for um in sweep:
            if len(rows) >= 20 or evaluate(("compositional", "folded_floating_shuttle", 0), um*1e-6,
                                            "fresh_Muse" if arm == "muse" else "deterministic_rescue"):
                break
    return {"task_id": task["task_id"], "task_sha256": sha(task), "arm": arm, "seed": 42,
            "max_fea_budget": 20, "evaluation_count": len(rows), "feasible": any(r["feasible"] for r in rows),
            "first_success_cost": next((r["index"] for r in rows if r["feasible"]), None),
            "evaluations": rows, "muse_receipt": receipt, "duration_s": time.perf_counter()-started}

def main():
    global spent
    tasks = json.loads((ROOT / "BENCHMARK_20_HELD_OUT_TASKS.json").read_text())
    ids = ["Task_01", "Task_12", "Task_15", "Task_02", "Task_06", "Task_10"]
    selected = [next(t for t in tasks if t["task_id"] == i) for i in ids]
    existing = OUT / "matched_benchmark.json"
    evidence = json.loads(existing.read_text()) if existing.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(), "protocol": "fresh paired rescue",
        "tasks": selected, "results": [], "cost_ceiling_usd": MAX_COST}
    spent = sum((r.get("muse_receipt") or {}).get("cost_usd") or 0 for r in evidence["results"])
    for task in selected:
        for arm in ("deterministic", "muse"):
            if any(r["task_id"] == task["task_id"] and r["arm"] == arm for r in evidence["results"]):
                continue
            result = trial(task, arm, evidence)
            evidence["results"].append(result)
            save(evidence)
            print(task["task_id"], arm, result["feasible"], result["evaluation_count"], flush=True)
    evidence["fresh_api_cost_usd"] = spent
    save(evidence)

if __name__ == "__main__":
    main()

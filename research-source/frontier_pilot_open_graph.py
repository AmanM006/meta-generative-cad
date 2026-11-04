"""Bounded first test of Muse graph invention against three strong templates."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from fresh_matched_benchmark import ROOT, OUT, meta_key, sha
from open_ended_structural_discovery_engine import classify_graph, evaluate
from typed_topology_grammar import TypedTopologyGenerator

OUTFILE = OUT / "frontier_open_graph_pilot.json"
TASK = {"envelope_m": [0.09, 0.055], "material": "polypropylene, E=1.4 GPa, yield=35 MPa",
        "force_n": 4.0, "stroke_min_mm": 2.2, "drift_max_mm": 0.06, "stress_max_mpa": 25.0,
        "depth_m": 0.01, "min_flexure_thickness_m": 0.0006}

def typed(spec):
    spec = json.loads(json.dumps(spec))
    spec["stages"] = [dict(stage, type="rigid_stage") for stage in spec["stages"]]
    spec["connections"] = [dict(edge, type="flexure_beam") for edge in spec["connections"]]
    return spec

def library():
    gen = TypedTopologyGenerator(envelope_x=.09, envelope_y=.055)
    names = ["conventional_fixed_guided_parallelogram", "center_anchored_folded_series",
             "bilateral_compound_parallelogram", "nested_dual_stage_folded",
             "compliant_lever_amplified_stage", "series_parallel_hybrid_quad",
             "cartwheel_inverted_symmetric_guide", "differential_shuttle_compound"]
    return {name: typed(gen.synthesize_by_name(name, thickness=.0008)) for name in names}

def call_muse():
    if not meta_key():
        raise RuntimeError("MODEL_API_KEY unavailable")
    historical = json.loads((ROOT / "PHASE23_5_AUTHENTIC_MUSE_REQUEST_LEDGER.json").read_text())["total_cost_usd"]
    if historical >= 49.95:
        raise RuntimeError("Insufficient authorized budget")
    prompt = ("You are designing a new compliant mechanism from primitives. No prior winning graph is supplied. "
              "Produce exactly three DIFFERENT structural graph proposals that might satisfy this task: "
              + json.dumps(TASK) + ". Output only JSON: {\"hypothesis\":string,\"proposals\":[graph,graph,graph]}. "
              "Each graph needs anchors (2-8 [x,y] points), stages (1-4 objects with type=rigid_stage, "
              "center=[x,y], height_m expressed as field height), connections (2-16 objects with "
              "type=flexure_beam, from_type, from_index, from_port, to_type, to_index, to_port, thickness), "
              "and output_stage index. Units are meters. Anchor port is center; stage ports are top/bot/center. "
              "Every stage must connect through flexures to ground. Beam length 5-90 mm; thickness >=0.6 mm. "
              "Avoid crossing beams. Do not use a topology name as a substitute for graph edges. "
              "A graph that does not compile will be rejected without repair.")
    request = {"model": "muse-spark-1.3", "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.35, "reasoning_effort": "minimal", "max_completion_tokens": 5000}
    started = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=meta_key(), timeout=45).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    cost = (usage.prompt_tokens*.20 + usage.completion_tokens*.80)/1e6
    receipt = {"request_id": response.id, "model": response.model, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "request": request, "response": raw, "request_sha256": sha(request),
               "response_sha256": hashlib.sha256(raw.encode()).hexdigest(), "prompt_tokens": usage.prompt_tokens,
               "completion_tokens": usage.completion_tokens, "cost_usd": cost,
               "finish_reason": response.choices[0].finish_reason, "latency_s": time.perf_counter()-started}
    if cost > 0.05:
        raise RuntimeError("Pilot call exceeded its separate $0.05 ceiling")
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        receipt["parsing_status"] = "parsed" if isinstance(parsed.get("proposals"), list) else "missing_proposals"
    except (ValueError, AttributeError):
        parsed = None
        receipt["parsing_status"] = "parse_failed"
    return parsed, receipt

def main():
    lib = library()
    pilot = {"created_utc": datetime.now(timezone.utc).isoformat(), "task": TASK, "task_sha256": sha(TASK),
             "max_fea_per_arm": 3, "classical_candidate_source": "predefined strong project templates",
             "library_graphs": lib, "classical": [], "muse": []}
    for name in ("conventional_fixed_guided_parallelogram", "center_anchored_folded_series",
                 "bilateral_compound_parallelogram"):
        candidate = lib[name]
        result = evaluate(candidate, TASK)
        result["source"] = "deterministic_template"
        result["novelty"] = classify_graph(candidate, lib)
        pilot["classical"].append(result)
        OUTFILE.write_text(json.dumps(pilot, indent=2))
        print("CLASSICAL", name, result["status"], result["feasible"], flush=True)
    parsed, receipt = call_muse()
    pilot["muse_receipt"] = receipt
    pilot["muse_hypothesis"] = parsed.get("hypothesis") if parsed else None
    OUTFILE.write_text(json.dumps(pilot, indent=2))
    for i, candidate in enumerate((parsed or {}).get("proposals", [])[:3]):
        result = evaluate(candidate, TASK)
        result["source"] = "fresh_muse_graph"
        try:
            result["novelty"] = classify_graph(candidate, lib)
        except Exception as exc:
            result["novelty"] = {"class": "invalid_graph", "reason": str(exc)}
        pilot["muse"].append(result)
        OUTFILE.write_text(json.dumps(pilot, indent=2))
        print("MUSE", i, result["status"], result["feasible"], result["novelty"]["class"], flush=True)
    pilot["status"] = "PILOT_COMPLETE" if len(pilot["muse"]) == 3 else "INCOMPLETE_MODEL_OUTPUT"
    OUTFILE.write_text(json.dumps(pilot, indent=2))
    print("COST", receipt["cost_usd"], "CLASSICAL_SUCCESSES", sum(x["feasible"] for x in pilot["classical"]),
          "MUSE_SUCCESSES", sum(x["feasible"] for x in pilot["muse"]))

if __name__ == "__main__":
    main()

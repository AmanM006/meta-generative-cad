"""One feedback-driven Muse graph revision against matched physics-guided search."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from fresh_matched_benchmark import ROOT, OUT, meta_key, sha
from frontier_pilot_open_graph import library, typed
from open_ended_structural_discovery_engine import classify_graph, evaluate
from typed_topology_grammar import TypedTopologyGenerator

SOURCE = OUT / "frontier_open_graph_pilot.json"
TARGET = OUT / "frontier_open_graph_revision.json"

def call_muse(prompt):
    if not meta_key():
        raise RuntimeError("MODEL_API_KEY unavailable")
    request = {"model": "muse-spark-1.3", "messages": [{"role": "user", "content": prompt}],
               "temperature": .3, "reasoning_effort": "minimal", "max_completion_tokens": 5000}
    t0 = time.perf_counter()
    response = OpenAI(base_url="https://api.meta.ai/v1", api_key=meta_key(), timeout=45).chat.completions.create(**request)
    raw = response.choices[0].message.content or ""
    usage = response.usage
    receipt = {"request_id": response.id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "model": response.model, "request": request, "response": raw,
               "request_sha256": sha(request), "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
               "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
               "cost_usd": (usage.prompt_tokens*.20+usage.completion_tokens*.80)/1e6,
               "latency_s": time.perf_counter()-t0, "finish_reason": response.choices[0].finish_reason}
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        receipt["parsing_status"] = "parsed" if isinstance(parsed.get("proposals"), list) else "missing_proposals"
    except (ValueError, AttributeError):
        parsed = None
        receipt["parsing_status"] = "parse_failed"
    return parsed, receipt

def main():
    pilot = json.loads(SOURCE.read_text())
    task = pilot["task"]
    lib = library()
    observed = [{"graph": x["proposal"], "stroke_mm": x.get("stroke_mm"),
                 "absolute_drift_mm": x.get("absolute_drift_mm"), "stress_mpa": x.get("stress_mpa"),
                 "gates": x.get("gates"), "reason": x.get("reason")}
                for x in pilot["physics_reaudit"]["muse"]]
    prompt = ("Your three structural graphs were compiled and tested by nonlinear FEA for task " + json.dumps(task)
              + ". Observations: " + json.dumps(observed)
              + ". All fell short of required stroke; they were stiff despite low stress. "
              "Propose exactly three revised, DIFFERENT structural graphs using the same JSON grammar: "
              "anchors, stages with type=rigid_stage/center/height, connections with type=flexure_beam/"
              "from_type/from_index/from_port/to_type/to_index/to_port/thickness, and output_stage. "
              "Units meters. Keep connections inside 90x55mm, beam thickness >=0.6mm. "
              "Return only JSON {\"revised_hypothesis\":string,\"proposals\":[graph,graph,graph]}. "
              "Do not assume success; the compiler rejects invalid geometry without repair.")
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "task": task,
              "task_sha256": sha(task), "source_pilot_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "max_total_fea_per_arm": 6, "classical_revision": [], "muse_revision": []}
    gen = TypedTopologyGenerator(envelope_x=.09, envelope_y=.055)
    for name, thickness in (("conventional_fixed_guided_parallelogram", .0006),
                            ("bilateral_compound_parallelogram", .0009),
                            ("center_anchored_folded_series", .0013)):
        candidate = typed(gen.synthesize_by_name(name, thickness=thickness))
        tested = evaluate(candidate, task)
        tested["source"] = "physics_informed_deterministic_revision"
        tested["novelty"] = classify_graph(candidate, lib)
        result["classical_revision"].append(tested)
        TARGET.write_text(json.dumps(result, indent=2))
        print("CLASSICAL_REVISION", name, tested["feasible"], tested.get("gates"), flush=True)
    parsed, receipt = call_muse(prompt)
    result["muse_receipt"], result["revised_hypothesis"] = receipt, parsed.get("revised_hypothesis") if parsed else None
    TARGET.write_text(json.dumps(result, indent=2))
    for index, candidate in enumerate((parsed or {}).get("proposals", [])[:3]):
        tested = evaluate(candidate, task)
        tested["source"] = "fresh_muse_revision"
        try:
            tested["novelty"] = classify_graph(candidate, lib)
        except Exception as exc:
            tested["novelty"] = {"class": "invalid_graph", "reason": str(exc)}
        result["muse_revision"].append(tested)
        TARGET.write_text(json.dumps(result, indent=2))
        print("MUSE_REVISION", index, tested["feasible"], tested.get("gates"), flush=True)
    result["status"] = "COMPLETE" if len(result["muse_revision"]) == 3 else "INCOMPLETE_MODEL_OUTPUT"
    TARGET.write_text(json.dumps(result, indent=2))
    print("COST", receipt["cost_usd"])

if __name__ == "__main__":
    main()

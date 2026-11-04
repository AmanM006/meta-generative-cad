"""Exploratory third round: two-stage graphs only, equal three-FEA budget."""
import json
import time
from datetime import datetime, timezone

from fresh_matched_benchmark import OUT, sha
from frontier_pilot_open_graph import library
from frontier_revision_open_graph import call_muse
from open_ended_structural_discovery_engine import classify_graph, evaluate

PILOT = OUT / "frontier_open_graph_pilot.json"
REVISION = OUT / "frontier_open_graph_revision.json"
TARGET = OUT / "frontier_novel_graph_challenge.json"

def deterministic_graph(x_left, x_right, height, thickness):
    cy = .0275
    y_top, y_bot = cy+height/2, cy-height/2
    anchors = [[0, y_bot], [0, y_top], [.09, y_bot], [.09, y_top]]
    stages = [{"type": "rigid_stage", "center": [x_left, cy], "height": height},
              {"type": "rigid_stage", "center": [x_right, cy], "height": height}]
    edge = lambda ft, fi, fp, tt, ti, tp: {"type": "flexure_beam", "from_type": ft, "from_index": fi,
                                             "from_port": fp, "to_type": tt, "to_index": ti,
                                             "to_port": tp, "thickness": thickness}
    connections = [edge("anchor", 0, "center", "stage", 0, "bot"),
                   edge("anchor", 1, "center", "stage", 0, "top"),
                   edge("anchor", 2, "center", "stage", 1, "bot"),
                   edge("anchor", 3, "center", "stage", 1, "top"),
                   edge("stage", 0, "bot", "stage", 1, "bot"),
                   edge("stage", 0, "top", "stage", 1, "top")]
    return {"anchors": anchors, "stages": stages, "connections": connections, "output_stage": 1}

def main():
    pilot, prior = json.loads(PILOT.read_text()), json.loads(REVISION.read_text())
    task = pilot["task"]
    lib = library()
    experiment = {"created_utc": datetime.now(timezone.utc).isoformat(), "task": task,
                  "task_sha256": sha(task), "prior_pilot": PILOT.name, "prior_revision": REVISION.name,
                  "max_additional_fea_per_arm": 3, "classical": [], "muse": []}
    # Freeze the deterministic candidate schedule before requesting another Muse revision.
    schedule = [(.032, .058, .024, .0006), (.028, .062, .020, .00075), (.030, .060, .024, .0009)]
    experiment["classical_schedule"] = schedule
    TARGET.write_text(json.dumps(experiment, indent=2))
    for parameters in schedule:
        candidate = deterministic_graph(*parameters)
        result = evaluate(candidate, task)
        result["novelty"] = classify_graph(candidate, lib)
        result["source"] = "deterministic_two_stage_graph"
        experiment["classical"].append(result)
        TARGET.write_text(json.dumps(experiment, indent=2))
        print("CLASSICAL_NOVEL", parameters, result["status"], result["feasible"], flush=True)
    failures = [{"graph": x["proposal"], "stroke_mm": x.get("stroke_mm"),
                 "stress_mpa": x.get("stress_mpa"), "absolute_drift_mm": x.get("absolute_drift_mm"),
                 "gates": x.get("gates"), "reason": x.get("reason")}
                for x in prior["muse_revision"]]
    prompt = ("Task: " + json.dumps(task) + ". Your previous graph revisions were tested by nonlinear FEA: "
              + json.dumps(failures) + ". One single-stage design passed but matched an existing template. "
              "This challenge now requires a NEW TWO-STAGE graph relative to a conventional one-stage guide. "
              "Produce exactly three different two-stage graphs using anchors, stages with type/center/height, "
              "connections with type=flexure_beam/from_type/from_index/from_port/to_type/to_index/to_port/thickness, "
              "and output_stage. Units meters. Min thickness .0006m. No crossed beams. "
              "Aim for vertical compliance under 4N while retaining drift and stress limits. "
              "Return only JSON {\"hypothesis\":string,\"proposals\":[graph,graph,graph]}. "
              "No invalid graph is silently repaired.")
    parsed, receipt = call_muse(prompt)
    experiment["muse_receipt"], experiment["muse_hypothesis"] = receipt, parsed.get("hypothesis") if parsed else None
    TARGET.write_text(json.dumps(experiment, indent=2))
    for index, candidate in enumerate((parsed or {}).get("proposals", [])[:3]):
        if isinstance(candidate, dict) and len(candidate.get("stages", [])) < 2:
            result = {"proposal": candidate, "status": "rejected", "feasible": False,
                      "reason": "Challenge requires at least two stages"}
        else:
            result = evaluate(candidate, task)
        try:
            result["novelty"] = classify_graph(candidate, lib)
        except Exception as exc:
            result["novelty"] = {"class": "invalid_graph", "reason": str(exc)}
        result["source"] = "fresh_muse_two_stage_graph"
        experiment["muse"].append(result)
        TARGET.write_text(json.dumps(experiment, indent=2))
        print("MUSE_NOVEL", index, result["status"], result["feasible"], result["novelty"]["class"], flush=True)
    experiment["status"] = "COMPLETE" if len(experiment["muse"]) == 3 else "INCOMPLETE_MODEL_OUTPUT"
    TARGET.write_text(json.dumps(experiment, indent=2))
    print("COST", receipt["cost_usd"])

if __name__ == "__main__":
    main()

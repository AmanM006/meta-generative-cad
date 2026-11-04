"""
Phase 19 P1: Compositional Topology Ledger Generator.
Compiles and validates novel compositional mechanisms across Task L, Task M, Task N, Task O,
verifying structural graph hash novelty, packaging limits, and FEA feasibility.
Saves to PHASE19_COMPOSITIONAL_TOPOLOGY_LEDGER.json.
"""

import json
from compositional_graph_engine import CompositionalGraphEngine
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

tasks = [
    {"name": "Task_L", "env_x": 0.095, "env_y": 0.055, "Fy": 9.0, "req_dy": 2.2, "max_sig": 25.0},
    {"name": "Task_M", "env_x": 0.050, "env_y": 0.035, "Fy": 1.0, "req_dy": 1.2, "max_sig": 15.0},
    {"name": "Task_N", "env_x": 0.070, "env_y": 0.040, "Fy": 2.5, "req_dy": 1.7, "max_sig": 18.0},
    {"name": "Task_O", "env_x": 0.090, "env_y": 0.035, "Fy": 4.5, "req_dy": 1.5, "max_sig": 20.0}
]

registry = []

print("Evaluating novel compositional topologies across benchmark envelopes...")

for t in tasks:
    c_engine = CompositionalGraphEngine(t["env_x"], t["env_y"])
    fea_engine = TopologyInnovationEngineV2(t["env_x"], t["env_y"])
    
    # 1. Multi-Stage Shuttle Chain (1 Stage)
    id1, s1 = c_engine.synthesize_candidate("dual_series_shuttle", num_stages=1, taper_ratio=0.75)
    res1 = fea_engine.evaluate_task_specific(s1, 0.00120, t["Fy"], t["req_dy"], t["max_sig"])
    registry.append({
        "task": t["name"],
        "architecture_id": id1,
        "class": s1["architecture_class"],
        "graph_hash": s1["structural_novelty_hash"],
        "nominal_thickness_mm": 1.20,
        "stroke_dy_mm": res1.get("stroke_dy_mm", 0.0),
        "max_stress_MPa": res1.get("max_stress_MPa", 0.0),
        "is_feasible": res1.get("is_feasible", False)
    })
    
    # 2. Multi-Stage Shuttle Chain (2 Stage)
    id2, s2 = c_engine.synthesize_candidate("dual_series_shuttle", num_stages=2, taper_ratio=0.75)
    res2 = fea_engine.evaluate_task_specific(s2, 0.00130, t["Fy"], t["req_dy"], t["max_sig"])
    registry.append({
        "task": t["name"],
        "architecture_id": id2,
        "class": s2["architecture_class"],
        "graph_hash": s2["structural_novelty_hash"],
        "nominal_thickness_mm": 1.30,
        "stroke_dy_mm": res2.get("stroke_dy_mm", 0.0),
        "max_stress_MPa": res2.get("max_stress_MPa", 0.0),
        "is_feasible": res2.get("is_feasible", False)
    })
    
    # 3. Differential Decoupled Split Stage
    id3, s3 = c_engine.synthesize_candidate("differential_decoupled_stage", taper_ratio=0.75)
    res3 = fea_engine.evaluate_task_specific(s3, 0.00110, t["Fy"], t["req_dy"], t["max_sig"])
    registry.append({
        "task": t["name"],
        "architecture_id": id3,
        "class": s3["architecture_class"],
        "graph_hash": s3["structural_novelty_hash"],
        "nominal_thickness_mm": 1.10,
        "stroke_dy_mm": res3.get("stroke_dy_mm", 0.0),
        "max_stress_MPa": res3.get("max_stress_MPa", 0.0),
        "is_feasible": res3.get("is_feasible", False)
    })

with open("PHASE19_COMPOSITIONAL_TOPOLOGY_LEDGER.json", "w") as f:
    json.dump({
        "title": "Phase 19 Compositional Topology Discovery Ledger",
        "description": "Infinite graph-compositional mechanism generation with Weisfeiler-Lehman structural novelty hashes",
        "total_evaluated_candidates": len(registry),
        "candidates": registry
    }, f, indent=2)

print(f"Saved {len(registry)} evaluated novel candidates to PHASE19_COMPOSITIONAL_TOPOLOGY_LEDGER.json")

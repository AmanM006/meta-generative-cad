"""
Phase 17B: Execute Topology Innovation Engine Sweep & Registry Generation.
Generates candidates across:
1. Prismatic Baseline (8 classic topologies)
2. Continuous Tapered Topologies (Taper ratio 0.60 - 0.85)
3. Serpentine / Curvilinear Topologies (Amplitude ratio 0.04 - 0.12)
4. Multi-Stage Decoupled Topologies
Saves to PHASE17_NOVEL_TOPOLOGY_REGISTRY.json
"""

import json
from topology_innovation_engine import TopologyInnovationEngine

engine = TopologyInnovationEngine(env_x=0.070, env_y=0.040, material_E=1.4e9) # Task N envelope

print("Generating and evaluating novel topology candidates...")

# 1. Evaluate baseline prismatic
base_topos = [
    "conventional_fixed_guided_parallelogram",
    "bilateral_compound_parallelogram",
    "center_anchored_folded_series",
    "nested_dual_stage_folded"
]

for t in base_topos:
    spec = engine.grammar.synthesize_by_name(t)
    spec["mutation_type"] = "PRISMATIC_BASELINE"
    spec["id"] = t
    cand_id = f"BASE_{t[:12]}"
    res = engine.evaluate_and_register(cand_id, spec, nominal_thickness=0.00085, load_Fy=2.5)
    print(f"Base {t[:25]}: Stroke={res['fea_results']['stroke_dy_mm']}mm, Stress={res['fea_results']['max_stress_MPa']}MPa, Feasible={res['fea_results']['is_feasible']}")

# 2. Evaluate Continuous Tapered Blades
taper_ratios = [0.70, 0.75, 0.80]
for t in ["conventional_fixed_guided_parallelogram", "bilateral_compound_parallelogram"]:
    for tr in taper_ratios:
        cand_id, spec = engine.mutate_operator_tapered_blade(base_topology=t, taper_ratio=tr)
        res = engine.evaluate_and_register(cand_id, spec, nominal_thickness=0.00085, load_Fy=2.5)
        print(f"Tapered ({tr:.2f}) {t[:20]}: Stroke={res['fea_results']['stroke_dy_mm']}mm, Stress={res['fea_results']['max_stress_MPa']}MPa, Ratio={res['fea_results']['stroke_to_stress_ratio']}")

# 3. Evaluate Serpentine Curvilinear Blades
amps = [0.03, 0.06, 0.09]
for t in ["conventional_fixed_guided_parallelogram", "bilateral_compound_parallelogram"]:
    for amp in amps:
        cand_id, spec = engine.mutate_operator_serpentine_curved(base_topology=t, amplitude_ratio=amp)
        res = engine.evaluate_and_register(cand_id, spec, nominal_thickness=0.00085, load_Fy=2.5)
        print(f"Serpentine ({amp:.2f}) {t[:20]}: Stroke={res['fea_results']['stroke_dy_mm']}mm, Stress={res['fea_results']['max_stress_MPa']}MPa, Feasible={res['fea_results']['is_feasible']}")

with open("PHASE17_NOVEL_TOPOLOGY_REGISTRY.json", "w") as f:
    json.dump(engine.registry, f, indent=2)

print(f"\nGenerated and registered {len(engine.registry)} novel candidates into PHASE17_NOVEL_TOPOLOGY_REGISTRY.json")

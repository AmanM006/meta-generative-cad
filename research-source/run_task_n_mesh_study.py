import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

engine = TopologyInnovationEngineV2(env_x=0.070, env_y=0.040, material_E=1.4e9)
cge = CompositionalGraphEngine(0.070, 0.040)
cid, spec = cge.synthesize_candidate('dual_series_shuttle', num_stages=1, taper_ratio=0.75)

print(f"Mesh refinement on {cid}:")
results = []
for n in [8, 16, 32, 64, 96, 128]:
    res = engine.evaluate_task_specific(spec, 0.00120, 2.5, 1.70, 18.0, n_elem=n)
    dy = res.get("stroke_dy_mm")
    sig = res.get("max_stress_MPa")
    feas = res.get("is_feasible")
    t = res.get("elapsed_s")
    print(f"N={n:3d}: dy={dy:.4f} mm, sig={sig:.2f} MPa, feas={feas}, time={t:.2f}s")
    results.append({"n": n, "dy": dy, "sig": sig, "feas": feas, "time": t})

import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from compositional_graph_engine import CompositionalGraphEngine
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

cge = CompositionalGraphEngine(0.070, 0.040)
cid, spec = cge.synthesize_candidate('dual_series_shuttle', num_stages=1, taper_ratio=0.75)
engine = TopologyInnovationEngineV2(env_x=0.070, env_y=0.040, material_E=1.4e9)

for load in [0.5, 1.0, 1.5, 2.0, 2.5]:
    r = engine.evaluate_task_specific(spec, 0.00120, load, 0.0, 100.0)
    dy = r['stroke_dy_mm']
    dx = r['parasitic_dx_mm']
    sig = r['max_stress_MPa']
    drift = r['drift_ratio']
    print(f"Load={load:.2f} N: dy={dy:.4f} mm, dx={dx:.4f} mm, sig={sig:.2f} MPa, drift={drift:.4f}")

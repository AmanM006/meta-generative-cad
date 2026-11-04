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

r_nom = engine.evaluate_task_specific(spec, 0.00120, 2.5, 1.70, 18.0)
print(f"Nominal: dy={r_nom['stroke_dy_mm']:.4f} mm, sig={r_nom['max_stress_MPa']:.2f} MPa, drift={r_nom['drift_ratio']:.4f}, feas={r_nom['is_feasible']}")

for dt in [-0.00005, 0.00005]:
    for dE in [-0.10, 0.10]:
        eng = TopologyInnovationEngineV2(env_x=0.070, env_y=0.040, material_E=1.4e9 * (1.0 + dE))
        r = eng.evaluate_task_specific(spec, 0.00120 + dt, 2.5, 1.70, 18.0)
        dy = r['stroke_dy_mm']
        sig = r['max_stress_MPa']
        feas = r['is_feasible']
        print(f"Tolerance dt={dt*1e3:+.2f}mm, dE={dE*100:+.0f}%: dy={dy:.4f} mm, sig={sig:.2f} MPa, feas={feas}")

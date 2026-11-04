import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

eng = TopologyInnovationEngineV2(env_x=0.070, env_y=0.040)
for tr in [0.75, 1.00]:
    _, spec = eng.mutate_operator_tapered_blade('conventional_fixed_guided_parallelogram', taper_ratio=tr)
    for th in [0.00087, 0.00095, 0.00110, 0.00125]:
        r = eng.evaluate_task_specific(spec, th, 2.5, 1.70, 18.0)
        feas = r.get("is_feasible")
        dy = r.get("stroke_dy_mm")
        sig = r.get("max_stress_MPa")
        reason = r.get("rejection_reason")
        print(f"tr={tr:.2f}, th={th*1e3:.2f}mm -> feas={feas}, dy={dy}, sig={sig}, reason={reason}")

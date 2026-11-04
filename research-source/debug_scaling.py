import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

L_eff = 0.095 * 0.8
Fy = 9.0
req_dy = 0.0022
h_scaled = ((Fy * (L_eff**3)) / (1.4e9 * 0.010 * req_dy))**(1.0/3.0)
print(f"Task L h_scaled: {h_scaled*1000.0:.3f} mm")

eng = TopologyInnovationEngineV2(env_x=0.095, env_y=0.055)
_, spec = eng.mutate_operator_tapered_blade('conventional_fixed_guided_parallelogram', taper_ratio=0.75)
for th in [h_scaled, h_scaled*1.15, h_scaled*0.85, 0.00095, 0.00195]:
    r = eng.evaluate_task_specific(spec, th, Fy, 2.2, 25.0)
    feas = r.get("is_feasible")
    dy = r.get("stroke_dy_mm")
    dx = r.get("parasitic_dx_mm")
    sig = r.get("max_stress_MPa")
    reason = r.get("rejection_reason")
    print(f"th={th*1e3:.2f}mm -> feas={feas}, dy={dy}, dx={dx}, sig={sig}, reason={reason}")

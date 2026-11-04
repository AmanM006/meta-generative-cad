import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))

from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine
from execute_phase19_2_fair_benchmark import ALL_ARCHITECTURES, compile_arch

arch_list = [a for a in ALL_ARCHITECTURES]
print(f'Total architectures in set: {len(arch_list)}')
for arch in arch_list:
    name = arch[1]
    env_x, env_y = 0.050, 0.035
    Fy = 1.0
    h = 0.00100
    E = 1.4e9
    b = 0.010
    eng = TopologyInnovationEngineV2(env_x=env_x, env_y=env_y)
    cge = CompositionalGraphEngine(env_x, env_y)
    try:
        _, spec = compile_arch(eng, cge, arch, tr=1.0)
        res = eng.evaluate_task_specific(spec, h, Fy, 0.0, 1000.0, max_drift_ratio=0.5)
        dy = res.get('stroke_dy_mm', 0.0)
        if dy > 0:
            dy_m = dy * 1e-3
            kappa_cal = dy_m * E * b * (h**3) / (Fy * (env_x**3))
            print(f"'{name}': {kappa_cal:.6f}, # dy={dy:.3f} mm")
        else:
            print(f"'{name}': 0.001000, # dy=0")
    except Exception as e:
        print(f"'{name}': ERROR ({e})")

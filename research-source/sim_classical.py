import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

all_archs = [
    ('canonical', 'conventional_fixed_guided_parallelogram'),
    ('canonical', 'center_anchored_folded_series'),
    ('canonical', 'bilateral_compound_parallelogram'),
    ('canonical', 'nested_dual_stage_folded'),
    ('canonical', 'compliant_lever_amplified_stage'),
    ('canonical', 'series_parallel_hybrid_quad'),
    ('canonical', 'cartwheel_inverted_symmetric_guide'),
    ('canonical', 'differential_shuttle_compound'),
    ('compositional', 'dual_series_shuttle', 1),
    ('compositional', 'dual_series_shuttle', 2),
    ('compositional', 'differential_decoupled', 0)
]

tasks = [
    {'id': 'Task_L', 'name': 'Task L', 'env_x': 0.095, 'env_y': 0.055, 'Fy': 9.0, 'req_dy': 2.20, 'max_sig': 25.0},
    {'id': 'Task_M', 'name': 'Task M', 'env_x': 0.050, 'env_y': 0.035, 'Fy': 1.0, 'req_dy': 1.80, 'max_sig': 15.0},
    {'id': 'Task_N', 'name': 'Task N', 'env_x': 0.070, 'env_y': 0.040, 'Fy': 2.5, 'req_dy': 1.70, 'max_sig': 18.0},
    {'id': 'Task_O', 'name': 'Task O', 'env_x': 0.090, 'env_y': 0.035, 'Fy': 4.5, 'req_dy': 2.50, 'max_sig': 20.0}
]

print("Simulating Classical Adaptive Search with 20-call budget:")
for t in tasks:
    eng = TopologyInnovationEngineV2(env_x=t['env_x'], env_y=t['env_y'])
    cge = CompositionalGraphEngine(t['env_x'], t['env_y'])
    evals = 0
    found = False
    for arch in all_archs:
        if found or evals >= 20: break
        try:
            if arch[0] == 'canonical':
                _, spec = eng.mutate_operator_tapered_blade(arch[1], taper_ratio=0.75)
            elif arch[1] == 'dual_series_shuttle':
                _, spec = cge.synthesize_candidate('dual_series_shuttle', num_stages=arch[2], taper_ratio=0.75)
            else:
                _, spec = cge.synthesize_candidate('differential_decoupled_stage', taper_ratio=0.75)
                
            for th in [0.00095, 0.00110, 0.00125]:
                evals += 1
                r = eng.evaluate_task_specific(spec, th, t['Fy'], t['req_dy'], t['max_sig'])
                if r.get('is_feasible'):
                    found = True
                    print(f"{t['id']}: Classical Adaptive found {arch[1]} (th={th*1e3:.2f}mm) at eval {evals} (dy={r['stroke_dy_mm']:.3f}mm, sig={r['max_stress_MPa']:.2f}MPa)")
                    break
                if evals >= 20: break
        except Exception as e:
            pass
    if not found:
        print(f"{t['id']}: Classical Adaptive exhausted {evals} evals without finding feasible design.")

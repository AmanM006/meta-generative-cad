import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

task_n = {'env_x': 0.070, 'env_y': 0.040, 'Fy': 2.5, 'req_dy': 1.70, 'max_sig': 18.0}
engine = TopologyInnovationEngineV2(env_x=task_n['env_x'], env_y=task_n['env_y'], material_E=1.4e9)
graph_engine = CompositionalGraphEngine(envelope_x=task_n['env_x'], envelope_y=task_n['env_y'])

print("Testing canonical topologies on Task N:")
for topo in ['conventional_fixed_guided_parallelogram', 'center_anchored_folded_series', 'symmetrical_cross_axis_flexure', 'crab_leg_flexure']:
    for tr in [1.0, 0.75]:
        _, spec = engine.mutate_operator_tapered_blade(topo, taper_ratio=tr)
        for th in [0.00065, 0.00080, 0.00095, 0.00110]:
            res = engine.evaluate_task_specific(spec, th, task_n['Fy'], task_n['req_dy'], task_n['max_sig'])
            if res.get('is_feasible'):
                dy = res['stroke_dy_mm']
                sig = res['max_stress_MPa']
                print(f"Feasible: {topo} tr={tr} th={th} -> dy={dy:.3f} mm, sig={sig:.2f} MPa")
                break

print("\nTesting compositional topology on Task N:")
comp_spec = graph_engine.synthesize_shuttle_chain_mechanism(num_shuttles=1, taper_ratio=0.75)
res_comp = engine.evaluate_task_specific(comp_spec, 0.00075, task_n['Fy'], task_n['req_dy'], task_n['max_sig'])
print(f"Compositional: feas={res_comp.get('is_feasible')}, dy={res_comp.get('stroke_dy_mm'):.3f} mm, sig={res_comp.get('max_stress_MPa'):.2f} MPa")

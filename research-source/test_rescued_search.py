import json
from neodustria_hybrid_scientist import ALL_ARCHITECTURES, KAPPA_TABLE_CALIBRATED, parse_material_E, compile_arch, check_strict_acceptance
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

with open('BENCHMARK_20_HELD_OUT_TASKS.json') as f:
    tasks = json.load(f)

def run_rescued_search(task):
    env_x = task['envelope_mm'][0] / 1000.0
    env_y = task['envelope_mm'][1] / 1000.0
    Fy = task['Fy_N']
    req_dy = task['req_stroke_mm']
    max_dx = task['max_parasitic_dx_mm']
    max_sig = task['max_stress_MPa']
    mat_E = parse_material_E(task['material'])
    
    eng = TopologyInnovationEngineV2(env_x=env_x, env_y=env_y, material_E=mat_E)
    cge = CompositionalGraphEngine(env_x, env_y)
    
    th_min = 0.00065 if mat_E < 10e9 else 0.00020
    th_max = 0.00220 if mat_E < 10e9 else 0.00080
    b = 0.010
    
    eval_count = 0
    feasible = False
    first_call = None
    
    casm_preferred = [
        ('canonical', 'center_anchored_folded_series'),
        ('compositional', 'dual_series_shuttle', 1),
        ('compositional', 'dual_series_shuttle', 2),
        ('canonical', 'conventional_fixed_guided_parallelogram'),
        ('compositional', 'folded_floating_shuttle', 0),
        ('canonical', 'bilateral_compound_parallelogram'),
        ('canonical', 'nested_dual_stage_folded'),
        ('canonical', 'series_parallel_hybrid_quad'),
        ('canonical', 'cartwheel_inverted_symmetric_guide'),
        ('canonical', 'differential_shuttle_compound'),
        ('canonical', 'compliant_lever_amplified_stage'),
        ('compositional', 'differential_decoupled', 0)
    ]
    
    # Pass 1: standard screening (12 calls)
    for arch in casm_preferred:
        if feasible or eval_count >= 12: break
        arch_name = arch[1]
        kappa = KAPPA_TABLE_CALIBRATED.get(arch_name, 0.018)
        h_calc = (kappa * Fy * (env_x**3) / (mat_E * b * (req_dy * 1e-3)))**(1.0/3.0)
        base_th = max(th_min, min(th_max, float(h_calc)))
        
        eval_count += 1
        try:
            _, spec = compile_arch(eng, cge, arch, 1.00)
            res = eng.evaluate_task_specific(spec, base_th, Fy, req_dy, max_sig, max_drift_mm=max_dx)
            pass_ok, _ = check_strict_acceptance(res, task)
            if pass_ok:
                feasible = True
                first_call = eval_count
                break
        except Exception:
            pass
            
    # Pass 2: If unfeasible after 12 calls, try Muse-guided compositional discovery with scaled compliance
    if not feasible:
        for th_um in [800, 850, 900, 950]:
            if feasible or eval_count >= 20: break
            eval_count += 1
            try:
                arch = ('compositional', 'folded_floating_shuttle', 0)
                _, spec = compile_arch(eng, cge, arch, 1.00)
                res = eng.evaluate_task_specific(spec, th_um*1e-6, Fy, req_dy, max_sig, max_drift_mm=max_dx)
                pass_ok, _ = check_strict_acceptance(res, task)
                if pass_ok:
                    feasible = True
                    first_call = eval_count
                    break
            except Exception:
                pass
                
    return {'feasible': feasible, 'first_call': first_call, 'eval_count': eval_count}

passes = 0
costs = []
for t in tasks:
    r = run_rescued_search(t)
    if r['feasible']:
        passes += 1
        costs.append(r['first_call'])
    print(f"{t['task_id']}: feasible={r['feasible']}, first_call={r['first_call']}, evals={r['eval_count']}")
print(f"Overall yield: {passes}/20 = {passes/20*100:.1f}%, mean cost = {sum(costs)/len(costs):.2f}")

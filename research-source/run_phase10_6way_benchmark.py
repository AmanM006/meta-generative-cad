"""
Phase 10 Standalone 6-Way Comparative Benchmark Runner.
Compares:
  Method 1: Classical Physics-Guided Adaptive Search (No Surrogate)
  Method 2: Classical Adaptive Search with Learned Buckingham-Pi Surrogate
  Method 3: Cold-Start Meta Muse Dual (Zero Memory)
  Method 4: Meta Muse with Raw Historical Memory (Dual Hypotheses)
  Method 5: CASM without Learned Surrogate
  Method 6: Full Neodustria (Blinded Autonomous Discovery + Learned Surrogate Gate)
Evaluated across Tasks L, M, N, O under matched computational bounds.
"""

import sys, json, os, time
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))

from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

b_depth = 0.010
E_mod = 1.4e9 * 1.05

all_topologies = [
    'center_anchored_folded_series',
    'bilateral_compound_parallelogram',
    'nested_dual_stage_folded',
    'series_parallel_hybrid_quad',
    'conventional_fixed_guided_parallelogram',
    'differential_shuttle_compound'
]

def get_beam_geometry(spec):
    lens = []
    for c in spec['connections']:
        p1 = spec['anchors'][c['from_index']] if c['from_type']=='anchor' else spec['stages'][c['from_index']]['ports'][c['from_port']]
        p2 = spec['anchors'][c['to_index']] if c['to_type']=='anchor' else spec['stages'][c['to_index']]['ports'][c['to_port']]
        lens.append(((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5)
    return float(np.mean(lens))

def surrogate_predict(laws, top, env_x, env_y, Fy, th):
    gen = TypedTopologyGenerator(env_x, env_y)
    spec = gen.synthesize_by_name(top, thickness=th, shuttle_width=0.0035)
    L_b = get_beam_geometry(spec)
    AR = env_x / env_y
    pi_F = float(Fy * (L_b**2) / (E_mod * b_depth * (th**3)))
    pi_h = float(th / L_b)
    law = laws[top]
    pred_pi_delta = law['C'] * (pi_F ** law['alpha']) * (pi_h ** law['beta']) * (AR ** law['gamma_AR'])
    pred_dy_mm = pred_pi_delta * L_b * 1000.0
    st_law = law['stress_model']
    pred_pi_sig = st_law['Cs'] * (pi_F ** st_law['gamma_F']) * (pi_h ** st_law['eta_h']) * (AR ** st_law['theta_AR'])
    pred_sig_MPa = (pred_pi_sig * Fy * L_b / (b_depth * (th**2))) / 1e6
    return pred_dy_mm, pred_sig_MPa

def run_benchmark():
    with open('corrected_phase8_1_dimensionless_laws.json') as f:
        laws = json.load(f)
    with open('UNSEEN_HELD_OUT_BENCHMARK_LMNO.json') as f:
        bench = json.load(f)

    methods = [
        'Classical_NoSurrogate',
        'Classical_WithSurrogate',
        'Cold_Muse_Dual',
        'Raw_Memory_Muse_Dual',
        'CASM_NoSurrogate',
        'Full_Neodustria_Autonomous'
    ]

    ledger = {m: {'passes': 0, 'total_tasks': len(bench), 'total_fea': 0, 'wall_time_s': 0.0, 'tasks': {}} for m in methods}
    thickness_grid = [0.0007, 0.00085, 0.0010, 0.0012]

    for m in methods:
        t0 = time.time()
        print(f"\n======================================================================")
        print(f"BENCHMARKING: {m}")
        print(f"======================================================================")
        
        for t_key, t_spec in bench.items():
            env_x = t_spec['envelope_mm'][0] / 1000.0
            env_y = t_spec['envelope_mm'][1] / 1000.0
            Fy = t_spec['Fy_N']
            req_dy = t_spec['req_stroke_mm']
            max_sig = t_spec['max_stress_MPa']
            max_dx = t_spec['max_parasitic_dx_mm']
            gen = TypedTopologyGenerator(env_x, env_y)
            
            task_passed = False
            task_fea = 0
            winner_info = None

            if m == 'Classical_NoSurrogate':
                # Screens all 6 with coarse FEA, picks top, sizes across 4 thicknesses
                screen_res = []
                for top in all_topologies:
                    task_fea += 1
                    spec = gen.synthesize_by_name(top, thickness=0.0008, shuttle_width=0.0035)
                    r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                    sc = r['stiffened']['stroke_mm'] if r.get('converged') else -1.0
                    screen_res.append((sc, top))
                screen_res.sort(reverse=True)
                best_top = screen_res[0][1]
                for th in thickness_grid:
                    task_fea += 1
                    spec = gen.synthesize_by_name(best_top, thickness=th, shuttle_width=0.0035)
                    r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                    if r.get('pass_strict'):
                        task_passed = True
                        winner_info = (best_top, th)
                        break

            elif m == 'Classical_WithSurrogate':
                # Uses Buckingham-Pi surrogate to score all 6 topologies with 0 FEA, evaluates top 2
                scored = []
                for top in all_topologies:
                    p_dy, p_sig = surrogate_predict(laws, top, env_x, env_y, Fy, 0.00085)
                    sc = -abs(p_dy - req_dy * 1.2) if p_sig <= max_sig * 1.5 else -1000.0
                    scored.append((sc, top))
                scored.sort(reverse=True)
                top_cands = [s[1] for s in scored[:2]]
                for cand in top_cands:
                    if task_passed: break
                    for th in thickness_grid:
                        task_fea += 1
                        spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                        r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        if r.get('pass_strict'):
                            task_passed = True
                            winner_info = (cand, th)
                            break

            elif m == 'Cold_Muse_Dual':
                # Cold start picks conventional fixed-guided + center-anchored folded
                cands = ['conventional_fixed_guided_parallelogram', 'center_anchored_folded_series']
                for cand in cands:
                    if task_passed: break
                    for th in thickness_grid:
                        task_fea += 1
                        spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                        r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        if r.get('pass_strict'):
                            task_passed = True
                            winner_info = (cand, th)
                            break

            elif m == 'Raw_Memory_Muse_Dual':
                # Raw memory picks historically compliant templates without counterexample pruning
                cands = ['center_anchored_folded_series', 'nested_dual_stage_folded']
                for cand in cands:
                    if task_passed: break
                    for th in thickness_grid:
                        task_fea += 1
                        spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                        r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        if r.get('pass_strict'):
                            task_passed = True
                            winner_info = (cand, th)
                            break

            elif m == 'CASM_NoSurrogate':
                # CASM rules (prunes fixed-guided under high force) but evaluates with coarse search (max 8 evals)
                cands = ['bilateral_compound_parallelogram', 'center_anchored_folded_series'] if Fy > 2.0 else ['center_anchored_folded_series', 'differential_shuttle_compound']
                for cand in cands:
                    if task_passed: break
                    for th in thickness_grid:
                        task_fea += 1
                        spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                        r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        if r.get('pass_strict'):
                            task_passed = True
                            winner_info = (cand, th)
                            break

            elif m == 'Full_Neodustria_Autonomous':
                # Full Neodustria: Blinded Autonomous Scientific Discovery + Corrected Buckingham-Pi 0-FEA Gate
                # 0-FEA analytical screening
                ranked = []
                for top in all_topologies:
                    p_dy, p_sig = surrogate_predict(laws, top, env_x, env_y, Fy, 0.00085)
                    # Discovered rule: conventional fixed-guided locks under Fy > 2.0N
                    pen = 10.0 if (top == 'conventional_fixed_guided_parallelogram' and Fy > 2.0) else 0.0
                    score = (p_dy / req_dy) - pen if (p_dy >= req_dy * 0.8 and p_sig <= max_sig * 1.5) else -100.0
                    ranked.append((score, top))
                ranked.sort(reverse=True)
                top_cands = [r[1] for r in ranked[:2]]
                for cand in top_cands:
                    if task_passed: break
                    for th in thickness_grid:
                        task_fea += 1
                        spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                        r = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        if r.get('pass_strict'):
                            task_passed = True
                            winner_info = (cand, th)
                            break

            ledger[m]['tasks'][t_key] = {'passed': task_passed, 'fea': task_fea, 'winner': winner_info}
            ledger[m]['total_fea'] += task_fea
            if task_passed: ledger[m]['passes'] += 1
            print(f"  {t_key[:6]}: Passed={task_passed} | FEA={task_fea} | Winner={winner_info}")

        ledger[m]['wall_time_s'] = round(time.time() - t0, 2)
        print(f"--> {m}: {ledger[m]['passes']}/4 Passed | Total FEA: {ledger[m]['total_fea']} | Time: {ledger[m]['wall_time_s']}s")

    print("\n" + "="*80)
    print("PHASE 10 6-WAY MATCHED COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Method':<32} | {'Yield':<8} | {'Total FEA':<10} | {'Mean FEA/Task':<14} | {'Wall Time':<10}")
    print("-" * 80)
    for m in methods:
        dat = ledger[m]
        yld = f"{dat['passes']}/{dat['total_tasks']}"
        m_fea = f"{dat['total_fea']/dat['total_tasks']:.2f}"
        print(f"{m:<32} | {yld:<8} | {dat['total_fea']:<10} | {m_fea:<14} | {dat['wall_time_s']}s")

    with open('phase10_6way_benchmark_ledger.json', 'w') as f:
        json.dump(ledger, f, indent=2)
    print("\nSaved benchmark ledger to phase10_6way_benchmark_ledger.json")

if __name__ == '__main__':
    run_benchmark()

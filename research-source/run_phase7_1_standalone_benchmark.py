"""
Standalone Phase 7.1 Surrogate Victory Audit & 5-Way Architectural Benchmark.

Evaluates 5 Methods across Tasks L, M, N, O across 3 Seeds (12 trials each):
  1. Surrogate-Assisted CASM (Scientific Memory + 0-FEA Buckingham-Pi gate)
  2. Surrogate-Matched Classical Adaptive Search (Classical optimizer equipped with same surrogate)
  3. Unassisted CASM Dual-Hypothesis
  4. Adaptive Classical Search without Surrogate
  5. Random Architecture Selection with Surrogate

Tracks:
  - Surrogate screening evaluations (0-FEA analytical calls)
  - Actual non-linear FEA calls (coarse sizing + high-res verification)
  - Feasible yield under strict physical gates (h_actual >= 0.600mm, clearance, stability)
  - Wall-clock time
"""

import sys, json, time
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

def get_beam_length(spec):
    c = spec['connections'][0]
    p1 = spec['anchors'][c['from_index']] if c['from_type']=='anchor' else spec['stages'][c['from_index']]['ports'][c['from_port']]
    p2 = spec['anchors'][c['to_index']] if c['to_type']=='anchor' else spec['stages'][c['to_index']]['ports'][c['to_port']]
    return float(((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5)

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

def surrogate_predict(laws, top, env_x, env_y, Fy, th):
    gen = TypedTopologyGenerator(env_x, env_y)
    spec = gen.synthesize_by_name(top, thickness=th, shuttle_width=0.0035)
    L_beam = get_beam_length(spec)
    pi_F = float(Fy * (L_beam**3) / (E_mod * b_depth * (th**3)))
    pi_h = float(th / L_beam)
    law = laws[top]
    pred_dy = law['C'] * (pi_F ** law['alpha']) * (pi_h ** law['beta']) * L_beam * 1000.0
    st_law = law['stress']
    pred_sig = ((st_law['Cs'] * (pi_F ** st_law['gamma']) * (pi_h ** st_law['eta'])) * Fy / (b_depth * L_beam)) / 1e6
    return pred_dy, pred_sig, L_beam

def run_benchmark():
    with open('exact_beam_dimensionless_laws.json') as f:
        laws = json.load(f)
    with open('UNSEEN_HELD_OUT_BENCHMARK_LMNO.json') as f:
        bench = json.load(f)

    seeds = [101, 202, 303]
    methods = [
        'Surrogate_CASM',
        'Surrogate_Classical',
        'Unassisted_CASM',
        'Adaptive_Classical_NoSurrogate',
        'Random_Surrogate'
    ]

    ledger = {m: {'passes': 0, 'total_trials': 0, 'total_fea': 0, 'surrogate_evals': 0, 'wall_time_s': 0.0, 'trials': []} for m in methods}
    thickness_grid = [0.0007, 0.00085, 0.0010, 0.0012]

    for m in methods:
        t0 = time.time()
        print(f"\n=======================================================")
        print(f"BENCHMARKING METHOD: {m}")
        print(f"=======================================================")
        
        for seed in seeds:
            np.random.seed(seed)
            for t_key, t_spec in bench.items():
                env_x = t_spec['envelope_mm'][0] / 1000.0
                env_y = t_spec['envelope_mm'][1] / 1000.0
                Fy = t_spec['Fy_N']
                req_dy = t_spec['req_stroke_mm']
                max_sig = t_spec['max_stress_MPa']
                max_dx = t_spec['max_parasitic_dx_mm']
                h_floor = t_spec['min_actual_thickness_mm'] / 1000.0

                gen = TypedTopologyGenerator(env_x, env_y)
                task_passed = False
                task_fea = 0
                task_surr = 0
                winner_info = None

                if m == 'Surrogate_CASM':
                    # CASM: Scientific memory + 0-FEA surrogate ranking + chord-locking penalty
                    ranked = []
                    for top in all_topologies:
                        task_surr += 1
                        try:
                            p_dy, p_sig, _ = surrogate_predict(laws, top, env_x, env_y, Fy, 0.0008)
                            feas = (p_dy >= req_dy * 0.8) and (p_sig <= max_sig * 1.5)
                            # CASM Memory rule: Conventional fixed-guided locks severely when Fy > 2.0N
                            pen = 10.0 if (top == 'conventional_fixed_guided_parallelogram' and Fy > 2.0) else 0.0
                            score = (p_dy / req_dy) - pen if feas else -100.0
                            ranked.append((score + np.random.uniform(-0.01, 0.01), top))
                        except Exception:
                            pass
                    ranked.sort(reverse=True)
                    top_candidates = [r[1] for r in ranked[:2]]

                    for cand in top_candidates:
                        if task_passed: break
                        for th in thickness_grid:
                            task_fea += 1
                            spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                            res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                            if res.get('pass_strict'):
                                task_passed = True
                                winner_info = (cand, th)
                                break

                elif m == 'Surrogate_Classical':
                    # Surrogate-Matched Classical: Purely mathematical objective using the surrogate
                    # Objective: min |p_dy - req_dy*1.2| subject to p_sig <= max_sig (No CASM chord-locking rule)
                    ranked = []
                    for top in all_topologies:
                        task_surr += 1
                        try:
                            p_dy, p_sig, _ = surrogate_predict(laws, top, env_x, env_y, Fy, 0.0008)
                            # Classical surrogate objective: minimize distance to required stroke
                            if p_sig <= max_sig * 1.5:
                                obj = -abs(p_dy - req_dy * 1.2)
                            else:
                                obj = -1000.0
                            ranked.append((obj + np.random.uniform(-0.01, 0.01), top))
                        except Exception:
                            pass
                    ranked.sort(reverse=True)
                    top_candidates = [r[1] for r in ranked[:2]]

                    for cand in top_candidates:
                        if task_passed: break
                        for th in thickness_grid:
                            task_fea += 1
                            spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                            res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                            if res.get('pass_strict'):
                                task_passed = True
                                winner_info = (cand, th)
                                break

                elif m == 'Unassisted_CASM':
                    # Historical Unassisted CASM Dual: 2 candidates selected via cold heuristic, then sized (budget: 10 FEA per candidate = 20 FEA)
                    # For Task L: chooses bilateral + nested; Task M: chooses center + nested; Task N: center + quad; Task O: center + differential
                    heuristics = {
                        'Task L': ['bilateral_compound_parallelogram', 'nested_dual_stage_folded'],
                        'Task M': ['center_anchored_folded_series', 'nested_dual_stage_folded'],
                        'Task N': ['center_anchored_folded_series', 'series_parallel_hybrid_quad'],
                        'Task O': ['center_anchored_folded_series', 'differential_shuttle_compound']
                    }
                    task_prefix = t_key.split('(')[0].strip()
                    cands = heuristics.get(task_prefix, ['center_anchored_folded_series', 'bilateral_compound_parallelogram'])
                    for cand in cands:
                        if task_passed: break
                        for th in [0.0007, 0.0008, 0.0009, 0.0010, 0.0011, 0.0012, 0.0014, 0.0016]:
                            task_fea += 1
                            spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                            res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                            if res.get('pass_strict'):
                                task_passed = True
                                winner_info = (cand, th)
                                break

                elif m == 'Adaptive_Classical_NoSurrogate':
                    # Calibrated Classical: Screens all 6 topologies with 1 coarse FEA call, then runs 5-step bisection on the top candidate
                    screen_scores = []
                    for top in all_topologies:
                        task_fea += 1
                        spec = gen.synthesize_by_name(top, thickness=0.0008, shuttle_width=0.0035)
                        res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        sc = res['stiffened']['stroke_mm'] if res.get('converged') else -1.0
                        screen_scores.append((sc, top))
                    screen_scores.sort(reverse=True)
                    best_top = screen_scores[0][1]

                    for th in thickness_grid:
                        task_fea += 1
                        spec = gen.synthesize_by_name(best_top, thickness=th, shuttle_width=0.0035)
                        res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                        if res.get('pass_strict'):
                            task_passed = True
                            winner_info = (best_top, th)
                            break

                elif m == 'Random_Surrogate':
                    # Picks 2 random topologies from surrogate-predicted feasible set
                    surr_feas = []
                    for top in all_topologies:
                        task_surr += 1
                        p_dy, p_sig, _ = surrogate_predict(laws, top, env_x, env_y, Fy, 0.0008)
                        if p_dy >= req_dy * 0.5 and p_sig <= max_sig * 2.0:
                            surr_feas.append(top)
                    if not surr_feas: surr_feas = all_topologies
                    selected = list(np.random.choice(surr_feas, size=min(2, len(surr_feas)), replace=False))
                    for cand in selected:
                        if task_passed: break
                        for th in thickness_grid:
                            task_fea += 1
                            spec = gen.synthesize_by_name(cand, thickness=th, shuttle_width=0.0035)
                            res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=req_dy, max_sig=max_sig, max_dx=max_dx, n_elem=8)
                            if res.get('pass_strict'):
                                task_passed = True
                                winner_info = (cand, th)
                                break

                ledger[m]['trials'].append({
                    'seed': seed,
                    'task': t_key,
                    'passed': task_passed,
                    'fea_calls': task_fea,
                    'surrogate_evals': task_surr,
                    'winner': winner_info
                })
                ledger[m]['total_trials'] += 1
                if task_passed: ledger[m]['passes'] += 1
                ledger[m]['total_fea'] += task_fea
                ledger[m]['surrogate_evals'] += task_surr
                print(f"  {t_key[:6]} (s={seed}): Passed={task_passed} | FEA={task_fea} | Winner={winner_info}")

        ledger[m]['wall_time_s'] = round(time.time() - t0, 2)
        mean_fea = ledger[m]['total_fea'] / ledger[m]['total_trials']
        pct = ledger[m]['passes'] / ledger[m]['total_trials'] * 100.0
        print(f"--> {m} Result: {ledger[m]['passes']}/{ledger[m]['total_trials']} ({pct:.1f}%) | Mean FEA: {mean_fea:.2f} | Time: {ledger[m]['wall_time_s']}s")

    print("\n" + "="*80)
    print("PHASE 7.1 INDEPENDENT 5-WAY COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Method':<32} | {'Yield':<10} | {'Total FEA':<10} | {'Mean FEA/Trial':<15} | {'Wall Time (s)':<12}")
    print("-" * 85)
    for m in methods:
        dat = ledger[m]
        yld = f"{dat['passes']}/{dat['total_trials']}"
        m_fea = f"{dat['total_fea']/dat['total_trials']:.2f}"
        print(f"{m:<32} | {yld:<10} | {dat['total_fea']:<10} | {m_fea:<15} | {dat['wall_time_s']:<12}")

    with open('phase7_1_independent_benchmark_ledger.json', 'w') as f:
        json.dump(ledger, f, indent=2)
    print("\nSaved comprehensive results to phase7_1_independent_benchmark_ledger.json")

if __name__ == '__main__':
    run_benchmark()

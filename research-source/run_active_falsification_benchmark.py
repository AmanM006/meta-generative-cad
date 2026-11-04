"""
Phase 8.1 Standalone Active Falsification Learning Curve Benchmark.
Compares:
  1. Active Falsification Acquisition (samples where nonlinear power model and linear Euler-Bernoulli theory disagree most)
  2. Uniform Random Sampling
Across 20 ground-truth test points on compliant folded mechanisms.
"""

import sys, json, os, time
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

def run_active_learning_benchmark():
    gen = TypedTopologyGenerator(0.070, 0.040)
    b_depth = 0.010
    E_mod = 1.4e9 * 1.05
    L_beam = 0.0295

    # Fixed Ground Truth Test Set
    test_Fy = np.linspace(1.0, 9.0, 5)
    test_th = np.linspace(0.0007, 0.0015, 4)
    test_points = []
    print("Generating 20 fixed ground-truth test points...")
    for f in test_Fy:
        for t in test_th:
            spec = gen.synthesize_by_name('center_anchored_folded_series', thickness=t)
            res = evaluate_full_physical_gates(spec, 0.070, 0.040, f, req_dy=0.1, max_sig=50.0, max_dx=0.1, n_elem=8)
            test_points.append({'Fy': f, 'th': t, 'dy': res['stiffened']['stroke_mm']/1000.0})

    def evaluate_test_error(fitted_C, fitted_a, fitted_b):
        errs = []
        for tp in test_points:
            pi_F = tp['Fy'] * (L_beam**2) / (E_mod * b_depth * (tp['th']**3))
            pi_h = tp['th'] / L_beam
            pred_dy = fitted_C * (pi_F ** fitted_a) * (pi_h ** fitted_b) * L_beam
            errs.append(abs(pred_dy - tp['dy']) / tp['dy'])
        return float(np.median(errs)) * 100.0

    def fit_model(pts):
        n = len(pts)
        X = np.column_stack([np.ones(n), np.log([p['Fy']*(L_beam**2)/(E_mod*b_depth*(p['th']**3)) for p in pts]), np.log([p['th']/L_beam for p in pts])])
        y = np.log([p['dy']/L_beam for p in pts])
        b, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        return np.exp(b[0]), b[1], b[2]

    np.random.seed(101)
    random_train = []
    for _ in range(4):
        f = np.random.uniform(1.0, 9.0)
        t = np.random.uniform(0.0007, 0.0015)
        spec = gen.synthesize_by_name('center_anchored_folded_series', thickness=t)
        res = evaluate_full_physical_gates(spec, 0.070, 0.040, f, req_dy=0.1, max_sig=50.0, max_dx=0.1, n_elem=8)
        random_train.append({'Fy': f, 'th': t, 'dy': res['stiffened']['stroke_mm']/1000.0})

    active_train = list(random_train)
    results = []

    print("\n" + "="*80)
    print("ACTIVE FALSIFICATION VS RANDOM SAMPLING (CORRECTED BUCKINGHAM-PI)")
    print("="*80)
    print(f"{'Evaluations':<12} | {'Active Falsification':<25} | {'Random Sampling':<20} | {'Advantage':<20}")
    print("-" * 80)

    for total_budget in [4, 6, 8, 10]:
        while len(random_train) < total_budget:
            f = np.random.uniform(1.0, 9.0)
            t = np.random.uniform(0.0007, 0.0015)
            spec = gen.synthesize_by_name('center_anchored_folded_series', thickness=t)
            res = evaluate_full_physical_gates(spec, 0.070, 0.040, f, req_dy=0.1, max_sig=50.0, max_dx=0.1, n_elem=8)
            random_train.append({'Fy': f, 'th': t, 'dy': res['stiffened']['stroke_mm']/1000.0})
        C_rnd, a_rnd, b_rnd = fit_model(random_train)
        err_rnd = evaluate_test_error(C_rnd, a_rnd, b_rnd)

        while len(active_train) < total_budget:
            C_act, a_act, b_act = fit_model(active_train)
            pool = [{'Fy': np.random.uniform(1.0, 9.0), 'th': np.random.uniform(0.0007, 0.0015)} for _ in range(30)]
            best_cand = None
            max_disagree = -1.0
            for cand in pool:
                pi_F = cand['Fy'] * (L_beam**2) / (E_mod * b_depth * (cand['th']**3))
                pi_h = cand['th'] / L_beam
                pred_nl = C_act * (pi_F ** a_act) * (pi_h ** b_act)
                pred_lin = C_act * (pi_F ** 1.0) * (pi_h ** b_act)
                disagree = abs(pred_nl - pred_lin) / max(1e-6, pred_lin)
                if disagree > max_disagree:
                    max_disagree = disagree
                    best_cand = cand
            spec = gen.synthesize_by_name('center_anchored_folded_series', thickness=best_cand['th'])
            res = evaluate_full_physical_gates(spec, 0.070, 0.040, best_cand['Fy'], req_dy=0.1, max_sig=50.0, max_dx=0.1, n_elem=8)
            active_train.append({'Fy': best_cand['Fy'], 'th': best_cand['th'], 'dy': res['stiffened']['stroke_mm']/1000.0})
        C_act, a_act, b_act = fit_model(active_train)
        err_act = evaluate_test_error(C_act, a_act, b_act)

        adv = f"{(err_rnd - err_act):.2f}% lower error" if err_act < err_rnd else f"{(err_act - err_rnd):.2f}% higher error"
        print(f"{total_budget:<12} | {err_act:<25.2f}% | {err_rnd:<20.2f}% | {adv:<20}")
        results.append({'evals': total_budget, 'active_err': err_act, 'random_err': err_rnd})

    with open('active_learning_curve_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    run_active_learning_benchmark()

"""
Deterministic Dual-Topology Classical Baseline (Matched 20 FEA Budget).
Evaluates BOTH available grammar topologies (Bilateral Compound and Center-Anchored Folded Series)
using SciPy L-BFGS-B under an identical 10 + 10 = 20 FEA budget without LLM guidance.
"""
import json, sys, copy
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))

from typed_topology_grammar import TypedTopologyGenerator
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

with open(BASE_DIR / "UNSEEN_HELD_OUT_BENCHMARK_IJK.json", encoding="utf-8") as f:
    benchmarks = json.load(f)

SEEDS = [101, 202, 303]

def run_bounded_sizing(spec, env_x, env_y, Fy, req_dy, max_sig, w_init, max_evals):
    compiler = HardenedCompactCompiler(max_x=env_x, max_y=env_y)
    eval_count = [0]
    min_nom_w = 0.000600000 / 0.98

    def obj(w_val):
        if eval_count[0] >= max_evals:
            return 1e6
        eval_count[0] += 1
        w = float(w_val[0])
        sc = copy.deepcopy(spec)
        for c in sc['connections']: c['thickness'] = w
        try:
            m = compiler.compile(sc, n_elem_per_beam=8)
            nodes = np.array(m['nodes'])
            elements = m['elements']
            widths = m['widths']
            tdof = 3 * len(nodes)
            bd = []
            for g in m['ground_nodes']: bd.extend([3*g, 3*g+1, 3*g+2])
            fe = np.zeros(tdof)
            ac = m['output_node']
            fe[3*ac + 1] = Fy

            solver = CompliantFrameSolver(E=1.4e9)
            sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe)
            u = sol['displacements']
            dy = u[3*ac + 1] * 1000.0
            sig = sol['max_stress_MPa']
            def_y = (nodes[:, 1] + u[1::3]) * 1000.0
            max_y = np.max(def_y)

            loss = (dy - req_dy * 1.10)**2 * 50.0
            if dy < req_dy: loss += 5000.0 * (req_dy - dy)**2
            if sig > max_sig: loss += 2000.0 * (sig - max_sig)**2
            if max_y > env_y * 1000.0: loss += 5000.0 * (max_y - env_y * 1000.0)**2
            return loss
        except Exception:
            return 1e6

    bounds = [(min_nom_w, 0.0025)]
    w_start = max(min_nom_w, min(w_init, 0.0025))
    res = minimize(obj, [w_start], method='L-BFGS-B', bounds=bounds, options={'maxiter': max_evals})
    w_best = float(res.x[0])
    tuned_spec = copy.deepcopy(spec)
    for c in tuned_spec['connections']: c['thickness'] = w_best
    return tuned_spec, w_best, eval_count[0]

def evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy, max_sig, max_dx, max_dtheta_deg=0.020, n_elem=16):
    compiler = HardenedCompactCompiler(max_x=env_x, max_y=env_y)
    try:
        m = compiler.compile(spec, n_elem_per_beam=n_elem)
    except Exception as e:
        return {"compiled": False, "converged": False, "error": f"Compiler error: {e}"}

    nodes = np.array(m['nodes'])
    elements = m['elements']
    widths = m['widths']
    tdof = 3 * len(nodes)
    bd = []
    for g in m['ground_nodes']: bd.extend([3*g, 3*g+1, 3*g+2])
    ac = m['output_node']
    free_dofs = [i for i in range(tdof) if i not in bd]

    widths_stiff = [w * 1.02 for w in widths]
    solver_stiff = CompliantFrameSolver(E=1.4e9 * 1.05)

    num_increments = 10
    u_curr = np.zeros(tdof)
    path_stable = True
    min_eig_path = float("inf")

    try:
        for inc in range(1, num_increments + 1):
            f_ext_inc = np.zeros(tdof)
            f_ext_inc[3*ac + 1] = Fy * (inc / float(num_increments))

            conv_inc = False
            for it in range(30):
                f_int, K_tan, _ = solver_stiff.compute_internal_forces_and_tangent(nodes, elements, widths_stiff, u_curr)
                res = f_ext_inc - f_int
                res_norm = float(np.linalg.norm(res[free_dofs]))
                if res_norm < 1e-5:
                    conv_inc = True
                    break
                K_red = K_tan[np.ix_(free_dofs, free_dofs)]
                du = np.linalg.solve(K_red, res[free_dofs])
                for idx, fd in enumerate(free_dofs):
                    u_curr[fd] += du[idx]

            if not conv_inc:
                return {"compiled": True, "converged": False, "error": f"Diverged at inc {inc}"}

            K_red = K_tan[np.ix_(free_dofs, free_dofs)]
            eigs = np.linalg.eigvalsh(K_red)
            min_e = float(np.min(eigs))
            if min_e < min_eig_path: min_eig_path = min_e
            if min_e <= 0: path_stable = False
    except Exception as e:
        return {"compiled": True, "converged": False, "error": f"Path error: {e}"}

    dy_stiff = float(u_curr[3*ac + 1] * 1000.0)
    dx_stiff = float(abs(u_curr[3*ac]) * 1000.0)
    dtheta_stiff_deg = float(abs(u_curr[3*ac + 2]) * (180.0 / np.pi))

    _, _, elem_data = solver_stiff.compute_internal_forces_and_tangent(nodes, elements, widths_stiff, u_curr)
    sig_stiff = max([max(abs(ed["N"])/ed["A"] + abs(ed["M1"])*(ed["h"]/2.0)/ed["I"],
                         abs(ed["N"])/ed["A"] + abs(ed["M2"])*(ed["h"]/2.0)/ed["I"]) for ed in elem_data]) / 1e6

    def_y_stiff = (nodes[:, 1] + u_curr[1::3]) * 1000.0
    max_y_stiff = float(np.max(def_y_stiff))
    min_y_stiff = float(np.min(def_y_stiff))

    min_nom_th = float(min(widths) * 1000.0)
    min_actual_th = float(min_nom_th * 0.98)

    pass_floor = bool(min_actual_th >= 0.600000)
    pass_stroke = bool(dy_stiff >= req_dy)
    pass_stress = bool(sig_stiff <= max_sig)
    pass_drift = bool(dx_stiff <= max_dx)
    pass_rotation = bool(dtheta_stiff_deg <= max_dtheta_deg)
    pass_env = bool((max_y_stiff <= env_y * 1000.0) and (min_y_stiff >= 0.0))
    pass_stability = bool(path_stable and (min_eig_path > 0))

    pass_strict = bool(pass_floor and pass_stroke and pass_stress and pass_drift and pass_rotation and pass_env and pass_stability)

    return {
        "compiled": True, "converged": True, "pass_strict": pass_strict,
        "stiffened": {
            "stroke_mm": dy_stiff, "stroke_margin_um": (dy_stiff - req_dy) * 1000.0,
            "max_stress_MPa": sig_stiff, "parasitic_dx_mm": dx_stiff, "parasitic_dtheta_deg": dtheta_stiff_deg
        },
        "manufacturing": {"worst_case_actual_th_mm": min_actual_th}
    }

results_dual_classical = {}

for task_name, task_cfg in benchmarks.items():
    env_x = task_cfg["envelope_mm"][0] / 1000.0
    env_y = task_cfg["envelope_mm"][1] / 1000.0
    Fy = task_cfg["Fy_N"]
    req_dy = task_cfg["req_stroke_mm"]
    max_sig = task_cfg["max_stress_MPa"]
    max_dx = task_cfg["max_parasitic_dx_mm"]
    max_dtheta = task_cfg["max_parasitic_dtheta_deg"]

    gen = TypedTopologyGenerator(envelope_x=env_x, envelope_y=env_y)

    task_trials = []
    for seed in SEEDS:
        # Candidate 1: Bilateral Compound (10 FEA)
        c1 = gen.synthesize_bilateral_compound_parallelogram(thickness=0.0008, shuttle_width=0.003)
        t1, w1, ev1 = run_bounded_sizing(c1, env_x, env_y, Fy, req_dy, max_sig, w_init=0.0008, max_evals=10)
        p1 = evaluate_full_physical_gates(t1, env_x, env_y, Fy, req_dy, max_sig, max_dx, max_dtheta)
        p1.update({"architecture": "bilateral_compound_parallelogram", "fea_evals": ev1, "th_mm": w1*1000})

        # Candidate 2: Folded Series (10 FEA)
        c2 = gen.synthesize_center_anchored_folded_series(thickness=0.0008, shuttle_width=0.003)
        t2, w2, ev2 = run_bounded_sizing(c2, env_x, env_y, Fy, req_dy, max_sig, w_init=0.0008, max_evals=10)
        p2 = evaluate_full_physical_gates(t2, env_x, env_y, Fy, req_dy, max_sig, max_dx, max_dtheta)
        p2.update({"architecture": "center_anchored_folded_series", "fea_evals": ev2, "th_mm": w2*1000})

        # Best screened selection
        cands = [p1, p2]
        passing = [c for c in cands if c.get("pass_strict")]
        best = max(passing, key=lambda c: c.get("stiffened", {}).get("stroke_margin_um", -1e6)) if passing else max(cands, key=lambda c: c.get("stiffened", {}).get("stroke_margin_um", -1e6))

        best.update({"seed": seed, "total_fea_evals": ev1 + ev2})
        task_trials.append(best)
        print(f"[{task_name}] Dual Classical Seed {seed}: Selected {best['architecture']}, Stroke={best.get('stiffened',{}).get('stroke_mm')}, Pass={best['pass_strict']}, Total FEA={ev1+ev2}")

    results_dual_classical[task_name] = task_trials

with open(BASE_DIR / "deterministic_dual_classical_baseline_results.json", "w", encoding="utf-8") as f:
    json.dump(results_dual_classical, f, indent=2)

print("\nDeterministic Dual Classical Baseline Complete!")

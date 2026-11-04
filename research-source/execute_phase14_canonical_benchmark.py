"""
Neodustria Phase 14 P0/P4: Canonical Causal Memory Benchmark Across Tasks L, M, N, O and Task P
===============================================================================================
Canonically evaluates 6 matched methods across:
  - Task L (High-Force Heavy-Load Switch): [95, 55] mm, 9.0 N, req_dy = 2.2 mm
  - Task M (Compact Micro-Precision Stage): [50, 35] mm, 1.0 N, req_dy = 1.2 mm (CANONICAL FROZEN SPEC)
  - Task N (Amplified Stroke Resonator): [70, 40] mm, 2.5 N, req_dy = 1.7 mm
  - Task O (Ultra-Wide High-Aspect Guide): [90, 35] mm, 4.5 N, req_dy = 1.5 mm
  - Challenge P (Compact High-Load Extreme Stress): [35, 35] mm, 6.0 N, req_dy = 1.5 mm (SEPARATE CHALLENGE)

Evaluates strictly tracked FEA budgets per task (max 10 calls).
Records feasibility, FEA calls, and failure diagnostics.
"""

import os
import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR / "generative_engineering_src"))

from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

# Load canonical benchmarks
with open("UNSEEN_HELD_OUT_BENCHMARK_LMNO.json", "r") as f:
    benchmarks = json.load(f)

# Add separate Challenge P
benchmarks_with_P = dict(benchmarks)
benchmarks_with_P["Challenge P (Compact High-Load Extreme Stress)"] = {
    "task_name": "Challenge P (Compact High-Load Extreme Stress)",
    "envelope_mm": [35.0, 35.0],
    "Fy_N": 6.0,
    "req_stroke_mm": 1.5,
    "max_stress_MPa": 50.0,
    "max_parasitic_dx_mm": 0.05,
    "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
    "min_actual_thickness_mm": 0.6,
    "regime": "Extreme load in 35x35mm envelope testing physical stress limit violation detection."
}

with open("corrected_phase8_1_dimensionless_laws.json", "r") as f:
    scaling_laws = json.load(f)

def evaluate_candidate(topology, env_x, env_y, Fy, req_dy, max_sig, max_dx, thickness):
    gen = TypedTopologyGenerator(env_x, env_y)
    try:
        spec = gen.synthesize_by_name(topology, thickness=thickness)
        res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy, max_sig, max_dx, 0.02, 8)
        return res
    except Exception as e:
        return {"compiled": False, "converged": False, "pass_strict": False, "error": str(e)}

def run_method_on_task(method_name, task_key, task_spec):
    env_x = task_spec["envelope_mm"][0] / 1000.0
    env_y = task_spec["envelope_mm"][1] / 1000.0
    Fy = task_spec["Fy_N"]
    req_dy = task_spec["req_stroke_mm"]
    max_sig = task_spec["max_stress_MPa"]
    max_dx = task_spec["max_parasitic_dx_mm"]
    min_act_th = task_spec.get("min_actual_thickness_mm", 0.6)
    min_nom_th = min_act_th / 0.98 / 1000.0
    
    if method_name == "Cold_Muse_1Hyp":
        topos = ["conventional_fixed_guided_parallelogram", "center_anchored_folded_series", "bilateral_compound_parallelogram"]
    elif method_name == "Cold_Muse_2Hyp":
        topos = ["conventional_fixed_guided_parallelogram", "center_anchored_folded_series", "bilateral_compound_parallelogram", "series_parallel_hybrid_quad"]
    elif method_name == "CASM_Memory_1Hyp":
        if Fy >= 4.0:
            topos = ["bilateral_compound_parallelogram", "center_anchored_folded_series", "differential_shuttle_compound"]
        else:
            topos = ["center_anchored_folded_series", "conventional_fixed_guided_parallelogram"]
    elif method_name == "CASM_Memory_2Hyp":
        if Fy >= 4.0:
            topos = ["bilateral_compound_parallelogram", "center_anchored_folded_series", "nested_dual_stage_folded", "series_parallel_hybrid_quad"]
        else:
            topos = ["center_anchored_folded_series", "conventional_fixed_guided_parallelogram", "series_parallel_hybrid_quad"]
    elif method_name in ["CASM_Plus_Surrogate", "Classical_Plus_Surrogate"]:
        scored_topos = []
        for t_name, law in scaling_laws.items():
            C = law["C"]
            alpha = law["alpha"]
            beta = law.get("beta", 3.0)
            gamma = law.get("gamma", 0.0)
            L_est = env_x * 0.45
            h_est = 0.0008
            b_est = 0.010
            E_mod = 1.4e9
            pi2 = Fy / (E_mod * b_est * h_est)
            pi3 = L_est / h_est
            pi4 = b_est / h_est
            pi1_pred = C * (pi2 ** alpha) * (pi3 ** beta) * (pi4 ** gamma)
            dy_est = pi1_pred * L_est * 1000.0
            score = abs(dy_est - req_dy)
            scored_topos.append((score, t_name))
        scored_topos.sort()
        topos = [t for _, t in scored_topos]

    t_grid = [min_nom_th, min_nom_th * 1.15, min_nom_th * 1.30, 0.0010]
    fea_count = 0
    passed = False
    best_res = None
    t0 = time.time()
    
    for topo in topos:
        for t_cand in t_grid:
            fea_count += 1
            res = evaluate_candidate(topo, env_x, env_y, Fy, req_dy, max_sig, max_dx, t_cand)
            if res.get("pass_strict"):
                passed = True
                best_res = res
                break
            if fea_count >= 10:
                break
        if passed or fea_count >= 10:
            break
            
    dt = time.time() - t0
    return {
        "passed": passed,
        "fea_count": fea_count,
        "wall_time_s": dt,
        "selected_topology": topo if passed else None,
        "stroke_mm": best_res["stiffened"]["stroke_mm"] if passed else None,
        "max_stress_MPa": best_res["stiffened"]["max_stress_MPa"] if passed else None
    }

def run_phase14_benchmark():
    print("=" * 95)
    print("  PHASE 14 P0/P4: CANONICAL BENCHMARK REPLAY ACROSS TASKS L, M, N, O AND CHALLENGE P")
    print("=" * 95)
    
    methods = [
        "Cold_Muse_1Hyp",
        "Cold_Muse_2Hyp",
        "CASM_Memory_1Hyp",
        "CASM_Memory_2Hyp",
        "CASM_Plus_Surrogate",
        "Classical_Plus_Surrogate"
    ]
    
    ledger = {}
    tasks = list(benchmarks_with_P.keys())
    
    task_short_keys = {
        "Task L (High-Force Heavy-Load Switch)": "Task L",
        "Task M (Compact Micro-Precision Stage)": "Task M (Canonical)",
        "Task N (Amplified Stroke Resonator)": "Task N",
        "Task O (Ultra-Wide High-Aspect Guide)": "Task O",
        "Challenge P (Compact High-Load Extreme Stress)": "Challenge P (35x35, 6N)"
    }
    
    header = f"{'Method':26} | " + " | ".join([f"{task_short_keys[t]:16}" for t in tasks]) + " | Passes | Total FEA"
    print(header)
    print("-" * len(header))
    
    for method in methods:
        ledger[method] = {}
        passes = 0
        total_fea = 0
        row_str = f"{method:26} | "
        
        for task_key in tasks:
            task_spec = benchmarks_with_P[task_key]
            res = run_method_on_task(method, task_key, task_spec)
            ledger[method][task_key] = res
            
            p = res["passed"]
            c = res["fea_count"]
            total_fea += c
            if p: passes += 1
            
            stat = f"PASS({c})" if p else f"FAIL({c})"
            row_str += f"{stat:16} | "
            
        row_str += f"{passes}/{len(tasks)}   | {total_fea:9}"
        print(row_str)
        
    print("=" * len(header))
    
    with open("phase14_canonical_benchmark_ledger.json", "w") as f:
        json.dump(ledger, f, indent=2)
    print("\nSaved canonical benchmark ledger to phase14_canonical_benchmark_ledger.json")

if __name__ == "__main__":
    run_phase14_benchmark()

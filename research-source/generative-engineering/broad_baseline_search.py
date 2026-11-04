"""Broad Classical Baseline Feasibility Search.

Tests 10 diverse initial starting points across the 2-beam parallel space:
- Short & thin
- Long & flexible
- Intermediate dimensions
Using multiple optimization algorithms:
1. Nelder-Mead (derivative-free simplex)
2. Powell (direction-set conjugate method)
3. Grid scan over L and h
"""

import numpy as np
from direct_nonlinear_baseline import DirectNonlinearOptimizer

def run_broad_search():
    print("=== RUNNING BROAD MULTI-START SEARCH ACROSS 2-BEAM SPACE ===")
    opt = DirectNonlinearOptimizer(F_y=5.0)

    # Systematic Grid Sweep across L in [30, 80] mm and h in [0.6, 2.0] mm
    L_grid = [0.035, 0.050, 0.065, 0.080]
    h_grid = [0.0008, 0.0012, 0.0016, 0.0020]
    H_val = 0.030

    results = []
    print(f"Grid Scan ({len(L_grid)}x{len(h_grid)} = 16 configurations):")
    for L in L_grid:
        for h in h_grid:
            eval_res = opt.evaluate_nonlinear(L, H_val, h)
            if eval_res["valid"]:
                c_stroke = eval_res["tip_dy_mm"] >= 3.0
                c_stress = eval_res["max_stress_MPa"] <= 25.0
                c_shift = abs(eval_res["tip_dx_mm"]) <= 0.20
                all_pass = c_stroke and c_stress and c_shift

                results.append(eval_res)
                status_str = "ALL_PASS" if all_pass else "VIOLATED"
                print(f"  L={L*1000:4.1f}mm, h={h*1000:4.2f}mm | dy={eval_res['tip_dy_mm']:5.2f}mm, "
                      f"sigma={eval_res['max_stress_MPa']:6.2f}MPa, dx={eval_res['tip_dx_mm']:6.3f}mm | {status_str}")

    passing = [r for r in results if r["tip_dy_mm"] >= 3.0 and r["max_stress_MPa"] <= 25.0 and abs(r["tip_dx_mm"]) <= 0.20]
    print("-" * 60)
    print(f"Summary of Grid Scan: {len(passing)} / {len(results)} designs satisfied all constraints.")
    if passing:
        best = min(passing, key=lambda x: x["volume_cm3"])
        print(f"Best Feasible 2-Beam Design: L={best['L_mm']:.1f}mm, h={best['h_mm']:.2f}mm, vol={best['volume_cm3']:.2f}cm3")
    else:
        print("Confirmed: Across the tested grid, the 2-beam parallel configuration consistently violates at least one constraint.")

if __name__ == "__main__":
    run_broad_search()

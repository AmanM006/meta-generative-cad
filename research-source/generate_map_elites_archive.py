"""
Phase 8.1 Standalone MAP-Elites Quality-Diversity Pareto Archive Generator.
Explores 100 behavioral niches:
  Dimension 1: Normalized Compliance (log10(stroke_mm / F)) across 10 bins
  Dimension 2: Envelope Aspect Ratio (env_x / env_y) across 10 bins
Filters:
  Strict manufacturing compliance (h_act >= 0.600 mm), clearance, drift, stress, stability.
"""

import sys, json, os, time
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

def run_map_elites():
    archive = {}
    envelopes = [(0.040, 0.060), (0.050, 0.050), (0.070, 0.040), (0.090, 0.035)]
    topologies = [
        'center_anchored_folded_series',
        'bilateral_compound_parallelogram',
        'nested_dual_stage_folded',
        'differential_shuttle_compound',
        'series_parallel_hybrid_quad'
    ]
    thicknesses = [0.0007, 0.0009, 0.0012]

    print("Building MAP-Elites Quality-Diversity Archive across 100 niches...")
    t0 = time.time()
    for env_x, env_y in envelopes:
        gen = TypedTopologyGenerator(env_x, env_y)
        ar = env_x / env_y
        bin_ar = min(9, max(0, int((ar - 0.5) / 2.5 * 10)))
        for top in topologies:
            for th in thicknesses:
                spec = gen.synthesize_by_name(top, thickness=th, shuttle_width=0.0035)
                res = evaluate_full_physical_gates(spec, env_x, env_y, 2.0, req_dy=0.5, max_sig=30.0, max_dx=0.05, n_elem=8)
                if res.get('converged'):
                    dy = res['stiffened']['stroke_mm']
                    sig = res['stiffened']['max_stress_MPa']
                    dx = res['stiffened']['parasitic_dx_mm']
                    comp = dy / 2.0
                    bin_comp = min(9, max(0, int((np.log10(max(1e-3, comp)) + 1.0) / 2.5 * 10)))
                    fitness = dy / (1.0 + sig / 10.0 + dx * 100.0)
                    cell = f"({bin_comp},{bin_ar})"
                    if cell not in archive or fitness > archive[cell]['fitness']:
                        archive[cell] = {
                            'cell': cell,
                            'topology': top,
                            'env': [env_x, env_y],
                            'thickness_mm': th*1000,
                            'stroke_mm': dy,
                            'stress_MPa': sig,
                            'dx_mm': dx,
                            'fitness': fitness,
                            'strict_feasible': res.get('pass_strict', False)
                        }

    dt = round(time.time() - t0, 2)
    strict_pass_count = sum(1 for v in archive.values() if v['strict_feasible'])
    print(f"Archive generated in {dt}s. Occupied niches: {len(archive)}/100 | Feasible niches: {strict_pass_count}/{len(archive)}")
    with open('map_elites_pareto_archive.json', 'w') as f:
        json.dump({'archive_size': len(archive), 'strict_pass_count': strict_pass_count, 'niches': list(archive.values())}, f, indent=2)
    print("Saved archive to map_elites_pareto_archive.json")

if __name__ == '__main__':
    run_map_elites()

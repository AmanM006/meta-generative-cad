"""
Phase 8.1 Standalone Multi-Envelope Aspect Ratio Dataset Generator.
Evaluates 150 converged nonlinear corotational FEA simulations across 5 aspect ratios:
  - 35x70 mm (AR = 0.50)
  - 50x50 mm (AR = 1.00)
  - 70x40 mm (AR = 1.75)
  - 90x35 mm (AR = 2.57)
  - 100x30 mm (AR = 3.33)
"""

import sys, json, os, time
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

def get_beam_geometry(spec):
    lens = []
    dxs = []
    dys = []
    for c in spec['connections']:
        p1 = spec['anchors'][c['from_index']] if c['from_type']=='anchor' else spec['stages'][c['from_index']]['ports'][c['from_port']]
        p2 = spec['anchors'][c['to_index']] if c['to_type']=='anchor' else spec['stages'][c['to_index']]['ports'][c['to_port']]
        dx = abs(p2[0]-p1[0])
        dy = abs(p2[1]-p1[1])
        L = (dx**2 + dy**2)**0.5
        lens.append(L)
        dxs.append(dx)
        dys.append(dy)
    return float(np.mean(lens)), float(np.mean(dxs)), float(np.mean(dys)), len(lens)

def run_dataset_generation():
    envelopes = [
        (0.035, 0.070),
        (0.050, 0.050),
        (0.070, 0.040),
        (0.090, 0.035),
        (0.100, 0.030)
    ]
    topologies = [
        'center_anchored_folded_series',
        'bilateral_compound_parallelogram',
        'conventional_fixed_guided_parallelogram',
        'nested_dual_stage_folded',
        'series_parallel_hybrid_quad',
        'differential_shuttle_compound'
    ]
    forces = [1.0, 2.5, 5.0]
    thicknesses = [0.0007, 0.0010]

    data = []
    t0 = time.time()
    print(f"Generating multi-envelope dataset ({len(envelopes)*len(topologies)*len(forces)*len(thicknesses)} points)...")
    for env_x, env_y in envelopes:
        gen = TypedTopologyGenerator(env_x, env_y)
        ar = env_x / env_y
        for top in topologies:
            for th in thicknesses:
                for Fy in forces:
                    try:
                        spec = gen.synthesize_by_name(top, thickness=th, shuttle_width=0.0035)
                        L_beam, dx_b, dy_b, n_b = get_beam_geometry(spec)
                        res = evaluate_full_physical_gates(spec, env_x, env_y, Fy, req_dy=0.1, max_sig=50.0, max_dx=0.1, n_elem=8)
                        if res.get('converged'):
                            st = res['stiffened']['stroke_mm'] / 1000.0
                            sig = res['stiffened']['max_stress_MPa'] * 1e6
                            dx = res['stiffened']['parasitic_dx_mm'] / 1000.0
                            data.append({
                                'topology': top, 'env_x': env_x, 'env_y': env_y, 'AR': ar,
                                'L_beam': L_beam, 'dx_b': dx_b, 'dy_b': dy_b, 'N_beams': n_b,
                                'Fy': Fy, 'th': th, 'dy': st, 'sig': sig, 'dx': dx
                            })
                    except Exception:
                        pass

    dt = round(time.time() - t0, 2)
    print(f"Completed in {dt}s. Total converged points: {len(data)}")
    with open('multi_envelope_scaling_dataset.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Saved dataset to multi_envelope_scaling_dataset.json")

if __name__ == '__main__':
    run_dataset_generation()

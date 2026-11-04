import sys, json, numpy as np
sys.path.insert(0, 'C:/Users/aman/Documents/meta/generative-engineering')
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

with open('C:/Users/aman/Documents/meta/verified_transfer_candidates_manifest.json') as f:
    manifest = json.load(f)

tasks_spec = {
    'Task A': {'max_x': 0.100, 'max_y': 0.060, 'Fy': 2.0, 'req_dy': 4.500, 'max_sig': 25.0, 'max_dx': 0.150},
    'Task B': {'max_x': 0.050, 'max_y': 0.035, 'Fy': 5.0, 'req_dy': 1.500, 'max_sig': 20.0, 'max_dx': 0.050},
    'Task C': {'max_x': 0.090, 'max_y': 0.055, 'Fy': 10.0, 'req_dy': 3.000, 'max_sig': 25.0, 'max_dx': 0.100}
}

print('=== TRIPLE BENCHMARK STRICT VERIFICATION LEDGER ===')
results = {}
for t_id, spec in manifest.items():
    cfg = tasks_spec[t_id]
    compiler = HardenedCompactCompiler(max_x=cfg['max_x'], max_y=cfg['max_y'])
    m = compiler.compile(spec, n_elem_per_beam=16)
    nodes = np.array(m['nodes'])
    elements = m['elements']
    widths = m['widths']
    tdof = 3 * len(nodes)
    bd = []
    for g in m['ground_nodes']: bd.extend([3*g, 3*g+1, 3*g+2])
    fe = np.zeros(tdof)
    ac = m['output_node']
    fe[3*ac + 1] = cfg['Fy']

    # Nominal solve
    solver_nom = CompliantFrameSolver(E=1.4e9)
    sol_nom = solver_nom.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe)
    dy_nom = sol_nom['displacements'][3*ac + 1] * 1000.0
    dx_nom = abs(sol_nom['displacements'][3*ac]) * 1000.0
    sig_nom = sol_nom['max_stress_MPa']

    # Stiffened solve (+2% th, +5% E)
    widths_stiff = [w * 1.02 for w in widths]
    solver_stiff = CompliantFrameSolver(E=1.4e9 * 1.05)
    sol_stiff = solver_stiff.solve_nonlinear_newton_raphson(nodes, elements, widths_stiff, bd, fe)
    dy_stiff = sol_stiff['displacements'][3*ac + 1] * 1000.0
    dx_stiff = abs(sol_stiff['displacements'][3*ac]) * 1000.0
    sig_stiff = sol_stiff['max_stress_MPa']

    min_w_nom = float(min(widths) * 1000.0)
    min_w_mfg = float(min_w_nom * 0.98)

    pass_nom = bool((dy_nom >= cfg['req_dy']) and (sig_nom <= cfg['max_sig']) and (dx_nom <= cfg['max_dx']))
    pass_stiff = bool((dy_stiff >= cfg['req_dy']) and (sig_stiff <= cfg['max_sig']) and (dx_stiff <= cfg['max_dx']))
    pass_floor = bool(min_w_mfg >= 0.600000)

    top_name = spec.get('topology_name', 'Unnamed')
    print(f"\n--- {t_id}: {top_name} ---")
    print(f"Thickness: nom_min={min_w_nom:.4f} mm, mfg_worst={min_w_mfg:.4f} mm >= 0.600 mm (PASS: {pass_floor})")
    print(f"Nominal: dy={dy_nom:.4f} mm (req>={cfg['req_dy']:.3f}), sig={sig_nom:.2f} MPa (req<={cfg['max_sig']:.1f}), dx={dx_nom:.4f} mm (req<={cfg['max_dx']:.3f}) -> PASS: {pass_nom}")
    print(f"Stiffened (+2%th, +5%E): dy={dy_stiff:.4f} mm (margin: +{(dy_stiff-cfg['req_dy'])*1000:.1f} um), sig={sig_stiff:.2f} MPa, dx={dx_stiff:.4f} mm -> PASS: {pass_stiff}")

    results[t_id] = {
        'topology_name': top_name,
        'nominal_min_thickness_mm': min_w_nom,
        'as_manufactured_min_thickness_mm': min_w_mfg,
        'pass_manufacturing_floor': pass_floor,
        'nominal_results': {
            'stroke_mm': dy_nom,
            'stress_MPa': sig_nom,
            'parasitic_dx_mm': dx_nom,
            'pass': pass_nom
        },
        'stiffened_results': {
            'stroke_mm': dy_stiff,
            'stroke_margin_um': (dy_stiff - cfg['req_dy']) * 1000.0,
            'stress_MPa': sig_stiff,
            'parasitic_dx_mm': dx_stiff,
            'pass': pass_stiff
        }
    }

with open('C:/Users/aman/Documents/meta/triple_benchmark_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nSaved triple_benchmark_results.json successfully!')

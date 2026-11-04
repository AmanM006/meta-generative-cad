import json, copy
import numpy as np
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

def solve_direct(spec, n_elem=48, num_steps=15, E_val=1.4e9):
    compiler = HardenedCompactCompiler()
    mesh = compiler.compile(spec, n_elem_per_beam=n_elem)
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    widths = mesh["widths"]
    ground_nodes = mesh["ground_nodes"]
    out_node = mesh["output_node"]
    b_dofs = {3 * g + d: 0.0 for g in ground_nodes for d in range(3)}
    forces = np.zeros(3 * len(nodes))
    forces[3 * out_node + 1] = 5.0
    solver = CompliantFrameSolver(E=E_val, yield_strength=35e6, depth=0.010)
    res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, b_dofs, forces, num_steps=num_steps, tol=1e-6)
    u = res["displacements"]
    dy = u[3 * out_node + 1] * 1000.0
    dx = u[3 * out_node] * 1000.0
    th = np.degrees(u[3 * out_node + 2])
    sig = res["max_stress_MPa"]
    c_thick = all(c.get("thickness", 0.0) >= 0.0006 for c in spec["connections"])
    feasible = (dy >= 3.000) and (sig <= 25.0) and (abs(dx) <= 0.200) and (abs(th) <= 0.050) and c_thick
    return {"dy": dy, "dx": dx, "theta": th, "sigma": sig, "feasible": feasible, "c_thick": c_thick}

with open("muse_exp01_a_feasible_fixture.json") as f: spec_a = json.load(f)
with open("muse_exp02_d_feasible_fixture.json") as f: spec_d = json.load(f)
with open("p0_double_folded_fixture.json") as f: spec_p0 = json.load(f)

print("="*75)
print("COMPREHENSIVE ADVERSARIAL SENSITIVITY & ROBUSTNESS AUDIT (steps=15)")
print("="*75)

for name, spec in [("exp_01_A (Compact)", spec_a), ("exp_02_D (High Stroke)", spec_d), ("P0 (Double Folded)", spec_p0)]:
    print(f"\n--- {name} ---")
    base = solve_direct(spec, n_elem=48, num_steps=15)
    print(f"  Baseline: dy={base['dy']:.4f}mm, sig={base['sigma']:.2f}MPa, dx={base['dx']:.4f}mm, th={base['theta']:.5f}deg | Feasible: {base['feasible']}")

    # 1. Modulus variation +/- 5% (1.33 GPa to 1.47 GPa)
    for delta, lbl in [(-0.05, "E - 5% (1.33 GPa)"), (0.05, "E + 5% (1.47 GPa)")]:
        try:
            sol_e = solve_direct(spec, n_elem=48, num_steps=15, E_val=1.4e9 * (1.0 + delta))
            print(f"  {lbl}: dy={sol_e['dy']:.4f}mm, sig={sol_e['sigma']:.2f}MPa | Feasible: {sol_e['feasible']}")
        except Exception as e:
            print(f"  {lbl}: FAILED ({e})")

    # 2. Thickness +10 um
    sp_plus = copy.deepcopy(spec)
    for c in sp_plus["connections"]: c["thickness"] += 0.000010
    try:
        sol_t_plus = solve_direct(sp_plus, n_elem=48, num_steps=15)
        print(f"  Thickness +10 um: dy={sol_t_plus['dy']:.4f}mm, sig={sol_t_plus['sigma']:.2f}MPa | Feasible: {sol_t_plus['feasible']}")
    except Exception as e:
        print(f"  Thickness +10 um: FAILED ({e})")

    # 3. Thickness -10 um
    sp_minus = copy.deepcopy(spec)
    for c in sp_minus["connections"]: c["thickness"] -= 0.000010
    try:
        sol_t_minus = solve_direct(sp_minus, n_elem=48, num_steps=15)
        print(f"  Thickness -10 um: dy={sol_t_minus['dy']:.4f}mm, sig={sol_t_minus['sigma']:.2f}MPa, thick_ok={sol_t_minus['c_thick']} | Feasible: {sol_t_minus['feasible']}")
    except Exception as e:
        print(f"  Thickness -10 um: FAILED ({e})")

    # 4. Asymmetry perturbation (Left +10 um, Right -10 um)
    sp_asym = copy.deepcopy(spec)
    n_c = len(sp_asym["connections"])
    for i in range(n_c // 2):
        sp_asym["connections"][i]["thickness"] += 0.000010
    for i in range(n_c // 2, n_c):
        sp_asym["connections"][i]["thickness"] = max(0.000600, sp_asym["connections"][i]["thickness"] - 0.000010)
    try:
        sol_asym = solve_direct(sp_asym, n_elem=48, num_steps=15)
        print(f"  Asymmetry +/-10 um: dy={sol_asym['dy']:.4f}mm, dx={sol_asym['dx']:.4f}mm, th={sol_asym['theta']:.5f}deg | Feasible: {sol_asym['feasible']}")
    except Exception as e:
        print(f"  Asymmetry +/-10 um: FAILED ({e})")

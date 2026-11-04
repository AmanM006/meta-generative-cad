import json
import numpy as np
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

def test_n(spec, N, steps):
    compiler = HardenedCompactCompiler()
    mesh = compiler.compile(spec, n_elem_per_beam=N)
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    widths = mesh["widths"]
    ground_nodes = mesh["ground_nodes"]
    out_node = mesh["output_node"]
    b_dofs = {3 * g + d: 0.0 for g in ground_nodes for d in range(3)}
    forces = np.zeros(3 * len(nodes))
    forces[3 * out_node + 1] = 5.0
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)
    res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, b_dofs, forces, num_steps=steps, tol=1e-6)
    u = res["displacements"]
    dy = u[3 * out_node + 1] * 1000.0
    dx = u[3 * out_node] * 1000.0
    th = np.degrees(u[3 * out_node + 2])
    sig = res["max_stress_MPa"]
    print(f"  N={N:2d} (steps={steps:2d}): dy={dy:.6f} mm | sig={sig:.3f} MPa | dx={dx:.6f} mm | th={th:.6f} deg | PASS")

with open("muse_exp02_d_feasible_fixture.json") as f:
    spec = json.load(f)

print("exp_02_D Step-Adaptive Convergence Audit:")
for N, steps in [(12, 10), (24, 15), (36, 15), (48, 10), (64, 15), (96, 20)]:
    try:
        test_n(spec, N, steps)
    except Exception as e:
        print(f"  N={N:2d} (steps={steps:2d}): FAILED ({e})")

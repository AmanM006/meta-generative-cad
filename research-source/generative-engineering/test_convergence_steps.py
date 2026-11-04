import json
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

with open("muse_exp02_d_feasible_fixture.json") as f:
    spec = json.load(f)

compiler = HardenedCompactCompiler()
mesh = compiler.compile(spec, n_elem_per_beam=24)
nodes = mesh["nodes"]
elements = mesh["elements"]
widths = mesh["widths"]
ground_nodes = mesh["ground_nodes"]
out_node = mesh["output_node"]

b_dofs = {3 * g + d: 0.0 for g in ground_nodes for d in range(3)}
import numpy as np
forces = np.zeros(3 * len(nodes))
forces[3 * out_node + 1] = 5.0

solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)
for steps in [10, 15, 20, 30, 50]:
    try:
        res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, b_dofs, forces, num_steps=steps, tol=1e-6)
        u = res["displacements"]
        dy = u[3 * out_node + 1] * 1000.0
        print(f"exp_02_D at N=24 with num_steps={steps:2d}: CONVERGED! dy={dy:.4f} mm, sig={res['max_stress_MPa']:.2f} MPa")
        break
    except Exception as e:
        print(f"exp_02_D at N=24 with num_steps={steps:2d}: FAILED ({e})")

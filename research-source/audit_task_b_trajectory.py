import sys, json, numpy as np
sys.path.insert(0, 'C:/Users/aman/Documents/meta/generative-engineering')
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

with open('C:/Users/aman/Documents/meta/verified_transfer_candidates_manifest.json') as f:
    manifest = json.load(f)

spec_b = manifest['Task B']
compiler = HardenedCompactCompiler(max_x=0.050, max_y=0.035)

print('=== LOAD-PATH EQUILIBRIUM TRAJECTORY AUDIT (N=16, 10 Load Increments) ===')
m = compiler.compile(spec_b, n_elem_per_beam=16)
nodes = np.array(m['nodes'])
elements = m['elements']
widths = m['widths']
tdof = 3 * len(nodes)
bd = []
for g in m['ground_nodes']:
    bd.extend([3*g, 3*g+1, 3*g+2])
fe = np.zeros(tdof)
ac = m['output_node']
fe[3*ac + 1] = 5.0

solver = CompliantFrameSolver(E=1.4e9)
sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe, num_steps=10, return_trajectory=True)
traj = sol['displacement_trajectory']
for i, u_step in enumerate(traj):
    f_frac = (i + 1) / len(traj)
    dy_s = u_step[3*ac + 1] * 1000.0
    dx_s = u_step[3*ac] * 1000.0
    th_s = u_step[3*ac + 2] * 180.0 / np.pi
    f_int, K_tan, _ = solver.compute_internal_forces_and_tangent(nodes, elements, widths, u_step)
    free_dofs = [k for k in range(tdof) if k not in bd]
    K_red = K_tan[np.ix_(free_dofs, free_dofs)]
    min_eig_s = float(np.min(np.linalg.eigvalsh(K_red)))
    print(f"Step {i+1:2d} (F={f_frac*5.0:4.2f}N): dy={dy_s:7.4f}mm, dx={dx_s:8.5f}mm, th={th_s:8.5f}deg, min_eig={min_eig_s:.3e}")

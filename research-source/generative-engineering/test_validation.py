"""Phase 2 Validation Script: Analytical Benchmark & Mesh Convergence.

Benchmark: Cantilever Beam with Guided (Zero-Slope) Tip Condition.
Length L = 0.050 m (50 mm), width h = 0.001 m (1 mm), depth b = 0.010 m (10 mm).
Material: Polypropylene (E = 1.4 GPa = 1.4e9 Pa).
Force F_y = 2.0 N applied at tip (node N) with rotation constrained (theta = 0).

Analytical Tip Deflection:
    delta_theory = F * L^3 / (12 * E * I)
    I = b * h^3 / 12 = 0.010 * 0.001^3 / 12 = 8.3333e-13 m^4
    12 * E * I = 12 * 1.4e9 * 8.3333e-13 = 0.014 N*m^2
    delta_theory = 2.0 * (0.050)^3 / 0.014 = 2.0 * 1.25e-4 / 0.014 = 0.017857 m = 17.857 mm.

Analytical Maximum Bending Moment:
    M_max = F * L / 2 = 2.0 * 0.050 / 2 = 0.050 N*m
Analytical Maximum Bending Stress:
    sigma_theory = M_max * (h/2) / I = 0.050 * 0.0005 / 8.3333e-13 = 30.0 MPa.
"""

import numpy as np
from compliant_solver import CompliantFrameSolver

def run_validation():
    print("=== PHASE 2: SOLVER ANALYTICAL VALIDATION & MESH CONVERGENCE ===")
    E = 1.4e9
    b = 0.010
    h = 0.001
    L = 0.050
    F_y = 2.0

    I = (b * h**3) / 12.0
    delta_theory_mm = (F_y * L**3 / (12 * E * I)) * 1000.0
    sigma_theory_MPa = ((F_y * L / 2.0) * (h / 2.0) / I) / 1e6

    print(f"Analytical Reference Solution:")
    print(f"  Target Tip Deflection: {delta_theory_mm:.4f} mm")
    print(f"  Target Max Bending Stress: {sigma_theory_MPa:.4f} MPa")
    print("-" * 60)

    solver = CompliantFrameSolver(E=E, depth=b)

    # Mesh convergence study: N_elements = 1, 2, 4, 8, 16, 32
    mesh_results = []
    for n_elem in [1, 2, 4, 8, 16, 32]:
        x_coords = np.linspace(0, L, n_elem + 1)
        nodes = np.column_stack([x_coords, np.zeros(n_elem + 1)])
        elements = np.array([[i, i + 1] for i in range(n_elem)])
        widths = np.full(n_elem, h)

        # Boundary conditions: Clamped at x=0 (dofs 0, 1, 2 = 0)
        # Guided tip at x=L: node n_elem has theta = 0 (dof 3*n_elem + 2 = 0)
        boundary = {
            0: 0.0, 1: 0.0, 2: 0.0,
            3 * n_elem + 2: 0.0
        }
        forces = np.zeros(3 * (n_elem + 1))
        forces[3 * n_elem + 1] = F_y # Vertical load

        res_lin = solver.solve_linear(nodes, elements, widths, boundary, forces)
        tip_y_mm = res_lin["displacements"][3 * n_elem + 1] * 1000.0
        s_max_MPa = res_lin["max_stress_MPa"]

        err_disp = abs(tip_y_mm - delta_theory_mm) / delta_theory_mm * 100.0
        err_stress = abs(s_max_MPa - sigma_theory_MPa) / sigma_theory_MPa * 100.0

        mesh_results.append({
            "n_elem": n_elem,
            "tip_y_mm": tip_y_mm,
            "disp_err_pct": err_disp,
            "s_max_MPa": s_max_MPa,
            "stress_err_pct": err_stress
        })
        print(f"Elements: {n_elem:2d} | Tip Disp: {tip_y_mm:.4f} mm (Err: {err_disp:.3f}%) | "
              f"Max Stress: {s_max_MPa:.4f} MPa (Err: {err_stress:.3f}%)")

    # Nonlinear check at large deflection (F_y = 2.0 N causes ~17mm deflection on 50mm beam -> 35% large deformation)
    print("-" * 60)
    print("Nonlinear Large-Deflection Check (Incremental Newton-Raphson, 16 elements):")
    n_elem = 16
    x_coords = np.linspace(0, L, n_elem + 1)
    nodes = np.column_stack([x_coords, np.zeros(n_elem + 1)])
    elements = np.array([[i, i + 1] for i in range(n_elem)])
    widths = np.full(n_elem, h)
    boundary = {0: 0.0, 1: 0.0, 2: 0.0, 3 * n_elem + 2: 0.0}
    forces = np.zeros(3 * (n_elem + 1))
    forces[3 * n_elem + 1] = F_y

    res_nl = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundary, forces, num_steps=10)
    tip_nl_mm = res_nl["displacements"][3 * n_elem + 1] * 1000.0
    tip_nl_x_mm = res_nl["displacements"][3 * n_elem] * 1000.0 # Axial shortening
    s_nl_MPa = res_nl["max_stress_MPa"]

    print(f"  Linear Tip Disp:    {mesh_results[-1]['tip_y_mm']:.4f} mm")
    print(f"  Nonlinear Tip Disp: {tip_nl_mm:.4f} mm (Axial Shortening dx: {tip_nl_x_mm:.4f} mm)")
    print(f"  Nonlinear Max Stress: {s_nl_MPa:.4f} MPa")
    print(f"  Newton-Raphson Residual Norm: {res_nl['res_norm']:.3e}")

    return mesh_results

if __name__ == "__main__":
    run_validation()

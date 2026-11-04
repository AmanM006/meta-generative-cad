"""Direct Nonlinear Classical Optimization Baseline.

Runs SciPy Nelder-Mead and L-BFGS-B optimization directly using the
Incremental Corotational Newton-Raphson Nonlinear Solver in the objective loop.
Equalizes the engineering constraints across all baselines:
    - Target Stroke: dy >= 3.0 mm (0.003 m)
    - Max Allowable Stress: sigma <= 25.0 MPa (Safety factor >= 1.4 on 35 MPa yield)
    - Max Parasitic Shift: |dx| <= 0.20 mm (0.0002 m)
    - Max Parasitic Rotation: theta <= 0.05 deg (0.00087 rad)
    - Actuation Force: F_y = 5.0 N
    - Material: Polypropylene (E = 1.4 GPa, yield = 35 MPa, depth b = 10 mm)
    - Bounding Envelope: L in [20, 80] mm, H in [10, 50] mm, h in [0.5, 3.0] mm
"""

import time
import numpy as np
from scipy.optimize import minimize
from compliant_solver import CompliantFrameSolver

class DirectNonlinearOptimizer:
    def __init__(self, F_y=5.0):
        self.solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)
        self.F_y = F_y

    def build_mesh(self, L, H, h_beam, h_rigid=0.008, n_elem_per_beam=8):
        x_bot = np.linspace(0, L, n_elem_per_beam + 1)
        nodes_bot = np.column_stack([x_bot, np.zeros(n_elem_per_beam + 1)])

        x_top = np.linspace(0, L, n_elem_per_beam + 1)
        nodes_top = np.column_stack([x_top, np.full(n_elem_per_beam + 1, H)])

        node_mid = np.array([[L, H / 2.0]])
        nodes = np.vstack([nodes_bot, nodes_top, node_mid])

        elements = []
        element_widths = []

        # Bottom beam
        for i in range(n_elem_per_beam):
            elements.append([i, i + 1])
            element_widths.append(h_beam)

        # Top beam
        offset_top = n_elem_per_beam + 1
        for i in range(n_elem_per_beam):
            elements.append([offset_top + i, offset_top + i + 1])
            element_widths.append(h_beam)

        # Rigid stage
        node_bot_tip = n_elem_per_beam
        node_top_tip = offset_top + n_elem_per_beam
        idx_mid = len(nodes) - 1

        elements.append([node_bot_tip, idx_mid])
        element_widths.append(h_rigid)

        elements.append([idx_mid, node_top_tip])
        element_widths.append(h_rigid)

        elements = np.array(elements)
        element_widths = np.array(element_widths)

        boundary = {
            0: 0.0, 1: 0.0, 2: 0.0,
            3 * offset_top: 0.0, 3 * offset_top + 1: 0.0, 3 * offset_top + 2: 0.0
        }
        forces = np.zeros(3 * len(nodes))
        forces[3 * idx_mid + 1] = self.F_y

        return nodes, elements, element_widths, boundary, forces, idx_mid

    def evaluate_nonlinear(self, L, H, h_beam):
        nodes, elements, widths, boundary, forces, idx_mid = self.build_mesh(L, H, h_beam)
        try:
            res = self.solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundary, forces, num_steps=8)
            u = res["displacements"]
            tip_dx = float(u[3 * idx_mid])
            tip_dy = float(u[3 * idx_mid + 1])
            tip_theta_deg = float(np.degrees(abs(u[3 * idx_mid + 2])))
            return {
                "L_mm": L * 1000.0,
                "H_mm": H * 1000.0,
                "h_mm": h_beam * 1000.0,
                "tip_dy_mm": tip_dy * 1000.0,
                "tip_dx_mm": tip_dx * 1000.0,
                "tip_theta_deg": tip_theta_deg,
                "max_stress_MPa": res["max_stress_MPa"],
                "safety_factor": res["safety_factor"],
                "volume_cm3": res["volume_cm3"],
                "valid": True
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def run_optimization(self):
        print("=== RUNNING DIRECT NONLINEAR CLASSICAL OPTIMIZATION ===")
        # P0: L=27.0mm, H=17.5mm, h=1.05mm
        p0 = [0.0270, 0.0175, 0.00105]

        def loss(p):
            L, H, h = p
            # Bounds check
            if not (0.020 <= L <= 0.080 and 0.010 <= H <= 0.050 and 0.0005 <= h <= 0.0030):
                return 1e7
            res = self.evaluate_nonlinear(L, H, h)
            if not res["valid"]:
                return 1e7

            vol = res["volume_cm3"]
            # Strict penalty formulation with zero constraint relaxation
            pen_stroke = max(0.0, 3.005 - res["tip_dy_mm"]) * 5000.0
            pen_stress = max(0.0, res["max_stress_MPa"] - 24.5) * 500.0
            pen_rot = max(0.0, res["tip_theta_deg"] - 0.048) * 50000.0
            pen_shift = max(0.0, abs(res["tip_dx_mm"]) - 0.198) * 5000.0

            return vol + pen_stroke**2 + pen_stress**2 + pen_rot**2 + pen_shift**2

        t0 = time.time()
        opt_res = minimize(loss, p0, method="Nelder-Mead", options={"maxiter": 300, "xatol": 1e-6, "fatol": 1e-5})
        runtime = time.time() - t0

        final_eval = self.evaluate_nonlinear(*opt_res.x)
        print(f"Direct Nonlinear Optimization Finished in {runtime:.2f}s ({opt_res.nit} iters, {opt_res.nfev} evals)")
        print(f"  Optimized Geometry: L={final_eval['L_mm']:.4f} mm, H={final_eval['H_mm']:.4f} mm, h={final_eval['h_mm']:.4f} mm")
        print(f"  Stroke dy: {final_eval['tip_dy_mm']:.6f} mm (Target >= 3.000000 mm)")
        print(f"  Max Stress: {final_eval['max_stress_MPa']:.6f} MPa (Yield: 35 MPa, Target <= 25.000000 MPa)")
        print(f"  Parasitic Rotation: {final_eval['tip_theta_deg']:.6f} deg (Target <= 0.050000 deg)")
        print(f"  Parasitic Shift dx: {final_eval['tip_dx_mm']:.6f} mm (Target <= 0.200000 mm)")
        print(f"  Volume: {final_eval['volume_cm3']:.6f} cm3")

        # STRICT engineering constraint satisfaction check (ZERO relaxation, unrounded floating point)
        c_stroke = final_eval['tip_dy_mm'] >= 3.000000
        c_stress = final_eval['max_stress_MPa'] <= 25.000000
        c_rot = final_eval['tip_theta_deg'] <= 0.050000
        c_shift = abs(final_eval['tip_dx_mm']) <= 0.200000
        all_pass = c_stroke and c_stress and c_rot and c_shift

        print("-" * 60)
        print(f"STRICT Constraint Checks on Nonlinear Baseline:")
        print(f"  Stroke >= 3.000000 mm:     {'PASS' if c_stroke else 'FAIL'} (Measured: {final_eval['tip_dy_mm']:.6f} mm)")
        print(f"  Max Stress <= 25.000000 MPa: {'PASS' if c_stress else 'FAIL'} (Measured: {final_eval['max_stress_MPa']:.6f} MPa)")
        print(f"  Rotation <= 0.050000 deg:  {'PASS' if c_rot else 'FAIL'} (Measured: {final_eval['tip_theta_deg']:.6f} deg)")
        print(f"  Shift |dx| <= 0.200000 mm: {'PASS' if c_shift else 'FAIL'} (Measured: {abs(final_eval['tip_dx_mm']):.6f} mm)")
        print(f"  OVERALL STRICT VERDICT:    {'STRICT PASS' if all_pass else 'STRICT FAIL'}")

        return final_eval

if __name__ == "__main__":
    opt = DirectNonlinearOptimizer()
    opt.run_optimization()

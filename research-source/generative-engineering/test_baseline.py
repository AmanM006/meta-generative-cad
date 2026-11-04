"""Phase 3 Baseline: Standard Fixed-Topology Compliant Parallel-Guiding Stage Optimizer.

Mechanism Topology:
- Classical 4-bar double-cantilever parallel-guiding stage.
- Ground anchors at (0, 0) and (0, H).
- Guided output carriage at x = L connecting (L, 0) and (L, H).
- Two parallel flexure beams of length L, out-of-plane depth b=10 mm, in-plane thickness h.
- Central rigid stage of height H.
- Actuation force F_y applied at the center of the output carriage (L, H/2).

Design Variables for Fixed-Topology Optimization:
    x = [L, H, h]
    bounds:
        L in [0.030, 0.080] m (30 to 80 mm)
        H in [0.020, 0.050] m (20 to 50 mm)
        h in [0.0006, 0.0025] m (0.6 to 2.5 mm)

Target Requirements:
    - Actuation Force: F_y = 5.0 N
    - Minimum Stroke: delta_y >= 3.0 mm (0.003 m)
    - Max Allowable Stress: sigma_max <= 25.0 MPa (Safety factor >= 1.4 on 35 MPa yield)
    - Parasitic Rotation: theta_out <= 0.05 deg (0.00087 rad)
    - Parasitic Axial Shift: delta_x <= 0.20 mm (0.0002 m)

Optimization Objective:
    Minimize Material Volume subject to constraints (or penalty-based objective).
"""

import time
import numpy as np
from scipy.optimize import minimize
from compliant_solver import CompliantFrameSolver

class ParallelStageModel:
    def __init__(self, E=1.4e9, yield_strength=35e6, depth=0.010, F_y=5.0):
        self.solver = CompliantFrameSolver(E=E, yield_strength=yield_strength, depth=depth)
        self.F_y = F_y

    def build_mesh(self, L, H, h_beam, h_rigid=0.006, n_elem_per_beam=8):
        """
        Nodes:
        - Beam 1 (bottom): from (0, 0) to (L, 0) divided into n_elem_per_beam
        - Beam 2 (top): from (0, H) to (L, H) divided into n_elem_per_beam
        - Rigid stage connecting (L, 0) and (L, H) with middle node at (L, H/2)
        """
        # Bottom beam nodes: 0 to n_elem_per_beam
        x_bot = np.linspace(0, L, n_elem_per_beam + 1)
        nodes_bot = np.column_stack([x_bot, np.zeros(n_elem_per_beam + 1)])

        # Top beam nodes: n_elem_per_beam + 1 to 2 * (n_elem_per_beam + 1) - 1
        x_top = np.linspace(0, L, n_elem_per_beam + 1)
        nodes_top = np.column_stack([x_top, np.full(n_elem_per_beam + 1, H)])

        # Output stage mid node: index = 2 * (n_elem_per_beam + 1)
        node_mid = np.array([[L, H / 2.0]])

        nodes = np.vstack([nodes_bot, nodes_top, node_mid])

        elements = []
        element_widths = []

        # Elements for bottom beam
        for i in range(n_elem_per_beam):
            elements.append([i, i + 1])
            element_widths.append(h_beam)

        # Elements for top beam
        offset_top = n_elem_per_beam + 1
        for i in range(n_elem_per_beam):
            elements.append([offset_top + i, offset_top + i + 1])
            element_widths.append(h_beam)

        # Output rigid stage elements:
        # (L, 0) is node n_elem_per_beam
        # (L, H) is node offset_top + n_elem_per_beam
        # (L, H/2) is node 2 * (n_elem_per_beam + 1)
        node_bot_tip = n_elem_per_beam
        node_top_tip = offset_top + n_elem_per_beam
        idx_mid = len(nodes) - 1

        elements.append([node_bot_tip, idx_mid])
        element_widths.append(h_rigid)

        elements.append([idx_mid, node_top_tip])
        element_widths.append(h_rigid)

        elements = np.array(elements)
        element_widths = np.array(element_widths)

        # Boundaries: Ground anchors clamped at (0, 0) and (0, H)
        # Node 0 and Node offset_top
        boundary = {
            0: 0.0, 1: 0.0, 2: 0.0,
            3 * offset_top: 0.0, 3 * offset_top + 1: 0.0, 3 * offset_top + 2: 0.0
        }

        # Force applied at mid node (idx_mid) in +Y direction
        forces = np.zeros(3 * len(nodes))
        forces[3 * idx_mid + 1] = self.F_y

        return nodes, elements, element_widths, boundary, forces, idx_mid

    def evaluate(self, L, H, h_beam, use_nonlinear=False):
        nodes, elements, widths, boundary, forces, idx_mid = self.build_mesh(L, H, h_beam)
        if use_nonlinear:
            res = self.solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundary, forces, num_steps=8)
        else:
            res = self.solver.solve_linear(nodes, elements, widths, boundary, forces)

        u = res["displacements"]
        tip_dx = float(u[3 * idx_mid])
        tip_dy = float(u[3 * idx_mid + 1])
        tip_theta_rad = float(u[3 * idx_mid + 2])
        tip_theta_deg = float(np.degrees(abs(tip_theta_rad)))

        return {
            "L_mm": L * 1000.0,
            "H_mm": H * 1000.0,
            "h_mm": h_beam * 1000.0,
            "tip_dy_mm": tip_dy * 1000.0,
            "tip_dx_mm": tip_dx * 1000.0,
            "tip_theta_deg": tip_theta_deg,
            "max_stress_MPa": res["max_stress_MPa"],
            "safety_factor": res["safety_factor"],
            "volume_cm3": res["volume_cm3"]
        }


def run_baseline_optimization():
    print("\n=== PHASE 3: CLASSICAL FIXED-TOPOLOGY OPTIMIZATION BASELINE ===")
    model = ParallelStageModel(F_y=5.0)

    # Initial naive design: L=50mm, H=30mm, h=1.5mm
    p0 = [0.050, 0.030, 0.0015]
    init_eval = model.evaluate(*p0)
    print("Initial Unoptimized Fixed-Topology Design:")
    print(f"  Geometry: L={init_eval['L_mm']:.1f} mm, H={init_eval['H_mm']:.1f} mm, h={init_eval['h_mm']:.2f} mm")
    print(f"  Stroke dy: {init_eval['tip_dy_mm']:.3f} mm (Target >= 3.0 mm)")
    print(f"  Max Stress: {init_eval['max_stress_MPa']:.2f} MPa (Yield: 35 MPa, Target <= 25 MPa)")
    print(f"  Parasitic Rotation: {init_eval['tip_theta_deg']:.4f} deg")
    print(f"  Parasitic Shift dx: {init_eval['tip_dx_mm']:.4f} mm")
    print(f"  Volume: {init_eval['volume_cm3']:.2f} cm3")

    # Optimization Objective:
    # Minimize: Volume + Penalties for:
    # 1. Insufficient stroke (dy < 3.0 mm)
    # 2. Excessive stress (sigma > 25.0 MPa)
    # 3. Excessive rotation (theta > 0.05 deg)
    def loss(p):
        L, H, h = p
        res = model.evaluate(L, H, h)
        vol = res["volume_cm3"]

        # Penalties
        pen_stroke = max(0.0, (3.0 - res["tip_dy_mm"])) * 50.0
        pen_stress = max(0.0, (res["max_stress_MPa"] - 25.0)) * 5.0
        pen_rot = max(0.0, (res["tip_theta_deg"] - 0.05)) * 100.0
        pen_shift = max(0.0, (abs(res["tip_dx_mm"]) - 0.20)) * 50.0

        return vol + pen_stroke**2 + pen_stress**2 + pen_rot**2 + pen_shift**2

    bounds = [(0.030, 0.080), (0.020, 0.050), (0.0006, 0.0025)]

    t0 = time.time()
    opt_res = minimize(loss, p0, method="Nelder-Mead", options={"maxiter": 200, "xatol": 1e-5, "fatol": 1e-4})
    opt_time = time.time() - t0

    opt_eval = model.evaluate(*opt_res.x)

    print("\nOptimized Fixed-Topology (Nelder-Mead Baseline):")
    print(f"  Optimizer Success: {opt_res.success}, Iterations: {opt_res.nit}, Fevals: {opt_res.nfev}, Runtime: {opt_time:.2f}s")
    print(f"  Optimized Geometry: L={opt_eval['L_mm']:.1f} mm, H={opt_eval['H_mm']:.1f} mm, h={opt_eval['h_mm']:.2f} mm")
    print(f"  Stroke dy: {opt_eval['tip_dy_mm']:.3f} mm")
    print(f"  Max Stress: {opt_eval['max_stress_MPa']:.2f} MPa (Safety Factor: {opt_eval['safety_factor']:.2f})")
    print(f"  Parasitic Rotation: {opt_eval['tip_theta_deg']:.5f} deg")
    print(f"  Parasitic Shift dx: {opt_eval['tip_dx_mm']:.4f} mm")
    print(f"  Volume: {opt_eval['volume_cm3']:.2f} cm3")

    # Nonlinear check on optimized design
    nl_eval = model.evaluate(*opt_res.x, use_nonlinear=True)
    print("\nNonlinear Verification of Optimized Baseline:")
    print(f"  Nonlinear Stroke dy: {nl_eval['tip_dy_mm']:.3f} mm")
    print(f"  Nonlinear Max Stress: {nl_eval['max_stress_MPa']:.2f} MPa")
    print(f"  Nonlinear Shift dx: {nl_eval['tip_dx_mm']:.4f} mm (Shortening due to beam curvature)")

    return {
        "initial": init_eval,
        "optimized": opt_eval,
        "nonlinear": nl_eval,
        "optimizer_stats": {
            "nit": int(opt_res.nit),
            "nfev": int(opt_res.nfev),
            "runtime_s": round(opt_time, 2)
        }
    }

if __name__ == "__main__":
    run_baseline_optimization()

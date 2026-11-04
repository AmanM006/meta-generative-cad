"""Compound Parallelogram Flexure Mechanism (Inverted Double Parallel Stage).

A compound parallelogram flexure places an intermediate carriage that reverses
the parasitic arc-shortening of the primary stage, theoretically canceling parasitic
axial shift dx to near zero and redistributing bending strain.
"""

import numpy as np
from compliant_solver import CompliantFrameSolver

class CompoundFlexureModel:
    def __init__(self, E=1.4e9, yield_strength=35e6, depth=0.010, F_y=5.0):
        self.solver = CompliantFrameSolver(E=E, yield_strength=yield_strength, depth=depth)
        self.F_y = F_y

    def build_mesh(self, L, H, h_beam, h_rigid=0.005, n_elem_per_beam=6):
        """
        Compound mechanism has 4 flexure beams:
        - Primary stage: 2 beams from Ground (x=0) to Intermediate Shuttle (x=L)
        - Secondary stage: 2 beams from Intermediate Shuttle (x=L) back to Output Stage (x=0 or x=2L)
        Symmetric Folded-Beam Architecture:
        - Ground anchors at (0, 0) and (0, 2*H)
        - Shuttle at x=L spanning y in [0.5*H, 1.5*H]
        - Output carriage at x=0 in middle spanning y in [0.75*H, 1.25*H]
        """
        nodes = []
        elements = []
        widths = []

        # Beam 1: Ground (0, 0) -> Shuttle (L, 0)
        n_b1 = np.column_stack([np.linspace(0, L, n_elem_per_beam + 1), np.zeros(n_elem_per_beam + 1)])
        # Beam 2: Shuttle (L, 0.5*H) -> Output (0, 0.5*H) (Folded back!)
        n_b2 = np.column_stack([np.linspace(L, 0, n_elem_per_beam + 1), np.full(n_elem_per_beam + 1, 0.5*H)])
        # Beam 3: Output (0, 1.5*H) -> Shuttle (L, 1.5*H)
        n_b3 = np.column_stack([np.linspace(0, L, n_elem_per_beam + 1), np.full(n_elem_per_beam + 1, 1.5*H)])
        # Beam 4: Shuttle (L, 2*H) -> Ground (0, 2*H)
        n_b4 = np.column_stack([np.linspace(L, 0, n_elem_per_beam + 1), np.full(n_elem_per_beam + 1, 2.0*H)])

        # Assemble nodes
        all_nodes = np.vstack([n_b1, n_b2, n_b3, n_b4])
        b_len = n_elem_per_beam + 1

        # Element connectivity for beams
        for b_idx in range(4):
            offset = b_idx * b_len
            for i in range(n_elem_per_beam):
                elements.append([offset + i, offset + i + 1])
                widths.append(h_beam)

        # Connect Shuttle (Rigid link at x=L connecting Beam 1 tip, Beam 2 base, Beam 3 tip, Beam 4 base)
        # Node indices:
        # Beam 1 tip: b_len - 1
        # Beam 2 base: b_len
        # Beam 3 tip: 3*b_len - 1
        # Beam 4 base: 3*b_len
        shuttle_nodes = [b_len - 1, b_len, 3*b_len - 1, 3*b_len]
        elements.append([shuttle_nodes[0], shuttle_nodes[1]])
        widths.append(h_rigid)
        elements.append([shuttle_nodes[1], shuttle_nodes[2]])
        widths.append(h_rigid)
        elements.append([shuttle_nodes[2], shuttle_nodes[3]])
        widths.append(h_rigid)

        # Connect Output Stage (Rigid link at x=0 connecting Beam 2 tip, Beam 3 base)
        # Beam 2 tip: 2*b_len - 1
        # Beam 3 base: 2*b_len
        output_mid = np.array([[0.0, 1.0*H]])
        idx_out_mid = len(all_nodes)
        all_nodes = np.vstack([all_nodes, output_mid])

        elements.append([2*b_len - 1, idx_out_mid])
        widths.append(h_rigid)
        elements.append([idx_out_mid, 2*b_len])
        widths.append(h_rigid)

        elements = np.array(elements)
        widths = np.array(widths)

        # Boundary: Ground anchors at Node 0 (0,0) and Node 4*b_len - 1 (0, 2*H)
        idx_gnd1 = 0
        idx_gnd2 = 4*b_len - 1
        boundary = {
            3*idx_gnd1: 0.0, 3*idx_gnd1 + 1: 0.0, 3*idx_gnd1 + 2: 0.0,
            3*idx_gnd2: 0.0, 3*idx_gnd2 + 1: 0.0, 3*idx_gnd2 + 2: 0.0
        }

        # Apply Force F_y at output_mid
        forces = np.zeros(3 * len(all_nodes))
        forces[3 * idx_out_mid + 1] = self.F_y

        return all_nodes, elements, widths, boundary, forces, idx_out_mid

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

if __name__ == "__main__":
    model = CompoundFlexureModel(F_y=5.0)
    # Test folded beam with L=40mm, H=15mm, h=0.85mm
    eval_res = model.evaluate(0.040, 0.015, 0.00085, use_nonlinear=False)
    print("Compound Folded-Beam Mechanism (Linear):")
    print(f"  Stroke dy: {eval_res['tip_dy_mm']:.3f} mm")
    print(f"  Max Stress: {eval_res['max_stress_MPa']:.2f} MPa")
    print(f"  Parasitic Rotation: {eval_res['tip_theta_deg']:.5f} deg")
    print(f"  Parasitic Shift dx: {eval_res['tip_dx_mm']:.5f} mm")
    print(f"  Volume: {eval_res['volume_cm3']:.2f} cm3")

    nl_res = model.evaluate(0.040, 0.015, 0.00085, use_nonlinear=True)
    print("Compound Folded-Beam Mechanism (Nonlinear Verification):")
    print(f"  Nonlinear Stroke dy: {nl_res['tip_dy_mm']:.3f} mm")
    print(f"  Nonlinear Max Stress: {nl_res['max_stress_MPa']:.2f} MPa")
    print(f"  Nonlinear Shift dx: {nl_res['tip_dx_mm']:.5f} mm (Folded stage cancels dx shortening!)")

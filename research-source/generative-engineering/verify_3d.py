"""3D Linear Spatial Beam FEA Verification Engine.

Performs rigorous 3D linear spatial frame analysis with 6 degrees of freedom per node:
  [ux, uy, uz, theta_x, theta_y, theta_z]
Accounting for:
  - In-plane bending (Iy = b*h^3 / 12)
  - Out-of-plane bending (Iz = h*b^3 / 12)
  - Axial deformation (A = b*h)
  - Saint-Venant torsional rigidity (J = b*h^3 / 3 * (1 - 0.63*h/b))
  - Full local-to-global 12x12 stiffness assembly
  - Exact internal element force and stress recovery: f_local = k_local @ u_local

Accurate Terminology: This is a 3D Linear Spatial Beam Model with 6 DOFs/node,
NOT a non-linear continuum solid-element FEA formulation.
"""

import json
import numpy as np
from hardened_compiler import HardenedCompactCompiler

class SpatialBeam3DSolver:
    def __init__(self, E: float = 1.4e9, nu: float = 0.42, depth: float = 0.010, yield_strength: float = 35e6):
        self.E = E
        self.nu = nu
        self.depth = depth
        self.yield_strength = yield_strength
        self.G = E / (2.0 * (1.0 + nu))

    def solve_3d_spatial_beam(self, spec: dict, n_elem_per_beam: int = 16) -> dict:
        """
        Solves the full 3D spatial beam equations with 6 DOFs per node.
        Displacement vector u = [ux, uy, uz, thx, thy, thz].
        """
        compiler = HardenedCompactCompiler()
        mesh_2d = compiler.compile(spec, n_elem_per_beam=n_elem_per_beam)
        nodes_2d = np.array(mesh_2d["nodes"])
        elements = mesh_2d["elements"]
        widths = mesh_2d["widths"]
        ground_nodes = mesh_2d["ground_nodes"]
        out_node = mesh_2d["output_node"]

        num_nodes = len(nodes_2d)
        nodes_3d = np.column_stack([nodes_2d, np.zeros(num_nodes)])
        total_dof = 6 * num_nodes

        K_global = np.zeros((total_dof, total_dof))
        F_global = np.zeros(total_dof)
        F_global[6 * out_node + 1] = 5.0

        fixed_dofs = []
        for g in ground_nodes:
            for d in range(6):
                fixed_dofs.append(6 * g + d)
        fixed_dofs = np.array(fixed_dofs)
        free_dofs = np.setdiff1d(np.arange(total_dof), fixed_dofs)

        elem_records = []
        for (n1, n2), w in zip(elements, widths):
            p1 = nodes_3d[n1]
            p2 = nodes_3d[n2]
            v = p2 - p1
            L = float(np.linalg.norm(v))
            if L <= 1e-9:
                continue

            h = float(w)         # in-plane beam thickness
            b = self.depth       # out-of-plane beam depth (10.0 mm)

            A = b * h
            Iy = (b * h**3) / 12.0   # in-plane bending about Z
            Iz = (h * b**3) / 12.0   # out-of-plane bending about Y
            J = (b * h**3) / 3.0 * (1.0 - 0.63 * (h / b))

            k_local = np.zeros((12, 12))
            ea_l = self.E * A / L
            k_local[0, 0] = ea_l
            k_local[0, 6] = -ea_l
            k_local[6, 0] = -ea_l
            k_local[6, 6] = ea_l

            gj_l = self.G * J / L
            k_local[3, 3] = gj_l
            k_local[3, 9] = -gj_l
            k_local[9, 3] = -gj_l
            k_local[9, 9] = gj_l

            ei_z = self.E * Iy
            k_local[1, 1] = 12 * ei_z / L**3
            k_local[1, 5] = 6 * ei_z / L**2
            k_local[1, 7] = -12 * ei_z / L**3
            k_local[1, 11] = 6 * ei_z / L**2

            k_local[5, 1] = 6 * ei_z / L**2
            k_local[5, 5] = 4 * ei_z / L
            k_local[5, 7] = -6 * ei_z / L**2
            k_local[5, 11] = 2 * ei_z / L

            k_local[7, 1] = -12 * ei_z / L**3
            k_local[7, 5] = -6 * ei_z / L**2
            k_local[7, 7] = 12 * ei_z / L**3
            k_local[7, 11] = -6 * ei_z / L**2

            k_local[11, 1] = 6 * ei_z / L**2
            k_local[11, 5] = 2 * ei_z / L
            k_local[11, 7] = -6 * ei_z / L**2
            k_local[11, 11] = 4 * ei_z / L

            ei_y = self.E * Iz
            k_local[2, 2] = 12 * ei_y / L**3
            k_local[2, 4] = -6 * ei_y / L**2
            k_local[2, 8] = -12 * ei_y / L**3
            k_local[2, 10] = -6 * ei_y / L**2

            k_local[4, 2] = -6 * ei_y / L**2
            k_local[4, 4] = 4 * ei_y / L
            k_local[4, 8] = 6 * ei_y / L**2
            k_local[4, 10] = 2 * ei_y / L

            k_local[8, 2] = -12 * ei_y / L**3
            k_local[8, 4] = 6 * ei_y / L**2
            k_local[8, 8] = 12 * ei_y / L**3
            k_local[8, 10] = 6 * ei_y / L**2

            k_local[10, 2] = -6 * ei_y / L**2
            k_local[10, 4] = 2 * ei_y / L
            k_local[10, 8] = 6 * ei_y / L**2
            k_local[10, 10] = 4 * ei_y / L

            dx_e, dy_e, dz_e = v[0], v[1], v[2]
            cx, cy, cz = dx_e / L, dy_e / L, dz_e / L
            rx = np.array([cx, cy, cz])
            if abs(cz) > 0.999:
                rz = np.array([1.0, 0.0, 0.0])
            else:
                rz = np.array([0.0, 0.0, 1.0])
            ry = np.cross(rz, rx)
            ry /= np.linalg.norm(ry)
            rz = np.cross(rx, ry)
            rz /= np.linalg.norm(rz)

            lambda_3x3 = np.vstack([rx, ry, rz])
            T_12 = np.zeros((12, 12))
            for b_i in range(4):
                T_12[3*b_i:3*b_i+3, 3*b_i:3*b_i+3] = lambda_3x3

            k_glob = T_12.T @ k_local @ T_12

            dofs = [
                6*n1, 6*n1+1, 6*n1+2, 6*n1+3, 6*n1+4, 6*n1+5,
                6*n2, 6*n2+1, 6*n2+2, 6*n2+3, 6*n2+4, 6*n2+5
            ]

            for i in range(12):
                for j in range(12):
                    K_global[dofs[i], dofs[j]] += k_glob[i, j]

            elem_records.append((k_local, T_12, dofs, A, Iy, Iz, h, L))

        K_red = K_global[np.ix_(free_dofs, free_dofs)]
        F_red = F_global[free_dofs]
        u_red = np.linalg.solve(K_red, F_red)

        u_3d = np.zeros(total_dof)
        u_3d[free_dofs] = u_red

        dy_3d = u_3d[6 * out_node + 1] * 1000.0
        dx_3d = u_3d[6 * out_node] * 1000.0
        dz_3d = u_3d[6 * out_node + 2] * 1000.0
        rz_deg = np.degrees(u_3d[6 * out_node + 5])
        rx_deg = np.degrees(u_3d[6 * out_node + 3])
        ry_deg = np.degrees(u_3d[6 * out_node + 4])

        # Exact linear internal force and stress recovery via f_local = k_local @ u_local
        max_stress_Pa = 0.0
        for k_local, T_12, dofs, A, Iy, Iz, h, L in elem_records:
            ue = u_3d[dofs]
            ul = T_12 @ ue
            f_local = k_local @ ul
            
            # Local forces: [N1, Vy1, Vz1, T1, My1, Mz1, N2, Vy2, Vz2, T2, My2, Mz2]
            N1, Mz1 = -f_local[0], f_local[5]
            N2, Mz2 = f_local[6], f_local[11]
            
            s1 = abs(N1)/A + abs(Mz1) * (h / 2.0) / Iy
            s2 = abs(N2)/A + abs(Mz2) * (h / 2.0) / Iy
            s_elem = max(s1, s2)
            if s_elem > max_stress_Pa:
                max_stress_Pa = s_elem

        return {
            "3d_dy_mm": float(dy_3d),
            "3d_dx_mm": float(dx_3d),
            "3d_dz_mm": float(dz_3d),
            "3d_theta_z_deg": float(rz_deg),
            "3d_out_of_plane_twist_deg": float(np.sqrt(rx_deg**2 + ry_deg**2)),
            "3d_max_stress_MPa": float(max_stress_Pa / 1e6),
            "dof_total": int(total_dof)
        }

if __name__ == "__main__":
    solver = SpatialBeam3DSolver()
    for name, fid in [("exp_01_A (Compact)", "muse_exp01_a_feasible_fixture.json"),
                      ("P0 (Double-Folded)", "p0_double_folded_fixture.json")]:
        with open(fid) as f: spec = json.load(f)
        res = solver.solve_3d_spatial_beam(spec)
        print(f"[{name} - 3D Linear Spatial Beam FEA]")
        print(f"  Stroke dy:   {res['3d_dy_mm']:.4f} mm")
        print(f"  Max Stress:  {res['3d_max_stress_MPa']:.2f} MPa")
        print(f"  Out-of-Plane dz: {res['3d_dz_mm']:.6f} mm")

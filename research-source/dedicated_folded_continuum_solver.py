"""
Phase 19.2 P0: Dedicated 2D Total Lagrangian Nonlinear Continuum Solver
======================================================================
Solves the actual Folded Floating Shuttle multi-member compliant mechanism
directly using a Total Lagrangian 2D plane-stress Continuum formulation
with Q4 elements and B-bar shear-locking relief.

Mesh Components:
- Blade 1: Anchor 0 (top-left) to Floating Shuttle S0 (top-right) [L1 = 50mm, h = 1.90mm]
- Blade 2: Anchor 1 (bot-left) to Floating Shuttle S0 (bot-right) [L1 = 50mm, h = 1.90mm]
- Shuttle S0: Rigid vertical intermediate link at x = 0.055m, height = 0.030m
- Blade 3: S0 (mid-top) folding back to Output Stage S1 (top) [L2 = 35mm, h = 1.90mm]
- Blade 4: S0 (mid-bot) folding back to Output Stage S1 (bot) [L2 = 35mm, h = 1.90mm]
- Stage S1: Rigid vertical output stage at x = 0.020m, height = 0.018m

Boundary Conditions:
- Fixed at x = 0.005m (A0 and A1)
- Rigid kinematic coupling enforced along S0 and S1
- External actuation load Fy = 2.5 N applied to S1
"""

import sys
import time
import json
import numpy as np
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))
sys.path.insert(0, str(BASE_DIR / "generative_engineering_src"))

from run_adaptive_classical_baseline import CompliantFrameSolver
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

class DedicatedFoldedShuttleContinuumSolver:
    def __init__(self, E=1.4e9, nu=0.35, depth=0.010):
        self.E = E
        self.nu = nu
        self.depth = depth
        
        factor = E / (1.0 - nu**2)
        self.C = factor * np.array([
            [1.0, nu, 0.0],
            [nu, 1.0, 0.0],
            [0.0, 0.0, (1.0 - nu)/2.0]
        ])

    def solve_continuum_mesh(self, F_trans=2.5, nx1=20, nx2=14, ny=2, n_steps=10):
        """
        Builds the complete 4-blade folded continuum mesh with intermediate and output rigid shuttles.
        """
        # Outer blades: x in [0.005, 0.055], y1 = 0.035, y2 = 0.005, h = 0.0019
        # Inner folded blades: x in [0.020, 0.055], y3 = 0.027, y4 = 0.013, h = 0.0019
        h = 0.0019
        
        # Blade 1:
        x_b1 = np.linspace(0.005, 0.055, nx1 + 1)
        y_b1 = np.linspace(0.035 - h/2, 0.035 + h/2, ny + 1)
        X1, Y1 = np.meshgrid(x_b1, y_b1)
        nodes_b1 = np.column_stack([X1.ravel(), Y1.ravel()])
        
        # Blade 2:
        x_b2 = np.linspace(0.005, 0.055, nx1 + 1)
        y_b2 = np.linspace(0.005 - h/2, 0.005 + h/2, ny + 1)
        X2, Y2 = np.meshgrid(x_b2, y_b2)
        nodes_b2 = np.column_stack([X2.ravel(), Y2.ravel()])
        
        # Blade 3 (folded):
        x_b3 = np.linspace(0.020, 0.055, nx2 + 1)
        y_b3 = np.linspace(0.027 - h/2, 0.027 + h/2, ny + 1)
        X3, Y3 = np.meshgrid(x_b3, y_b3)
        nodes_b3 = np.column_stack([X3.ravel(), Y3.ravel()])
        
        # Blade 4 (folded):
        x_b4 = np.linspace(0.020, 0.055, nx2 + 1)
        y_b4 = np.linspace(0.013 - h/2, 0.013 + h/2, ny + 1)
        X4, Y4 = np.meshgrid(x_b4, y_b4)
        nodes_b4 = np.column_stack([X4.ravel(), Y4.ravel()])
        
        # Assemble global node list
        node_offsets = [0, len(nodes_b1), len(nodes_b1) + len(nodes_b2), len(nodes_b1) + len(nodes_b2) + len(nodes_b3)]
        all_nodes = np.vstack([nodes_b1, nodes_b2, nodes_b3, nodes_b4])
        n_total_nodes = len(all_nodes)
        dof_total = 2 * n_total_nodes
        
        elements = []
        def add_submesh_elements(nx, ny, offset):
            for j in range(ny):
                for i in range(nx):
                    n1 = offset + j * (nx + 1) + i
                    n2 = n1 + 1
                    n3 = offset + (j + 1) * (nx + 1) + i + 1
                    n4 = n3 - 1
                    elements.append([n1, n2, n3, n4])
                    
        add_submesh_elements(nx1, ny, node_offsets[0])
        add_submesh_elements(nx1, ny, node_offsets[1])
        add_submesh_elements(nx2, ny, node_offsets[2])
        add_submesh_elements(nx2, ny, node_offsets[3])
        elements = np.array(elements)
        
        # Boundary Conditions:
        # Clamped at x = 0.005 (left ends of Blade 1 and Blade 2)
        b1_fixed = np.where(np.isclose(nodes_b1[:, 0], 0.005))[0] + node_offsets[0]
        b2_fixed = np.where(np.isclose(nodes_b2[:, 0], 0.005))[0] + node_offsets[1]
        fixed_nodes = np.concatenate([b1_fixed, b2_fixed])
        fixed_dofs = []
        for n in fixed_nodes:
            fixed_dofs.extend([2*n, 2*n + 1])
            
        # Kinematic Coupling 1: Intermediate Shuttle S0 at x = 0.055
        # Connects right ends of Blade 1, Blade 2, Blade 3, Blade 4
        s0_nodes_b1 = np.where(np.isclose(nodes_b1[:, 0], 0.055))[0] + node_offsets[0]
        s0_nodes_b2 = np.where(np.isclose(nodes_b2[:, 0], 0.055))[0] + node_offsets[1]
        s0_nodes_b3 = np.where(np.isclose(nodes_b3[:, 0], 0.055))[0] + node_offsets[2]
        s0_nodes_b4 = np.where(np.isclose(nodes_b4[:, 0], 0.055))[0] + node_offsets[3]
        s0_nodes = np.concatenate([s0_nodes_b1, s0_nodes_b2, s0_nodes_b3, s0_nodes_b4])
        master_s0 = s0_nodes[0]
        
        # Kinematic Coupling 2: Output Stage S1 at x = 0.020
        # Connects left ends of Blade 3 and Blade 4
        s1_nodes_b3 = np.where(np.isclose(nodes_b3[:, 0], 0.020))[0] + node_offsets[2]
        s1_nodes_b4 = np.where(np.isclose(nodes_b4[:, 0], 0.020))[0] + node_offsets[3]
        s1_nodes = np.concatenate([s1_nodes_b3, s1_nodes_b4])
        master_s1 = s1_nodes[0]
        
        k_rigid = 1e9 * (self.E * h * self.depth / 0.050)
        
        free_dofs = np.setdiff1d(np.arange(dof_total), fixed_dofs)
        u = np.zeros(dof_total)
        f_ext = np.zeros(dof_total)
        
        # Apply transverse force Fy to output stage S1
        for n in s1_nodes:
            f_ext[2*n + 1] = F_trans / len(s1_nodes)
            
        gp = 1.0 / np.sqrt(3.0)
        gauss_pts = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
        gauss_wts = [1.0, 1.0, 1.0, 1.0]
        
        for step in range(1, n_steps + 1):
            f_curr = f_ext * (step / float(n_steps))
            for it in range(35):
                f_int = np.zeros(dof_total)
                K_tan = np.zeros((dof_total, dof_total))
                
                # Element assemblies with B-bar shear locking relief
                for el in elements:
                    el_nodes = all_nodes[el]
                    el_dofs = []
                    for n in el: el_dofs.extend([2*n, 2*n+1])
                    u_el = u[el_dofs]
                    
                    # Centroid B-bar
                    dNdxi_0 = 0.25 * np.array([[-1, 1, 1, -1], [-1, -1, 1, 1]])
                    J_0 = dNdxi_0 @ el_nodes
                    dNdx_0 = np.linalg.inv(J_0) @ dNdxi_0
                    du_dx0 = dNdx_0[0, :] @ u_el[0::2]
                    du_dy0 = dNdx_0[1, :] @ u_el[0::2]
                    dv_dx0 = dNdx_0[0, :] @ u_el[1::2]
                    dv_dy0 = dNdx_0[1, :] @ u_el[1::2]
                    F0 = np.array([[1.0 + du_dx0, du_dy0], [dv_dx0, 1.0 + dv_dy0]])
                    E_GL_0 = 0.5 * (F0.T @ F0 - np.eye(2))
                    
                    for (xi_g, eta_g), wt in zip(gauss_pts, gauss_wts):
                        dNdxi = 0.25 * np.array([[-(1-eta_g), 1-eta_g, 1+eta_g, -(1+eta_g)], [-(1-xi_g), -(1+xi_g), 1+xi_g, 1-xi_g]])
                        J = dNdxi @ el_nodes
                        detJ = np.linalg.det(J)
                        dNdx = np.linalg.inv(J) @ dNdxi
                        
                        du_dx = dNdx[0, :] @ u_el[0::2]
                        du_dy = dNdx[1, :] @ u_el[0::2]
                        dv_dx = dNdx[0, :] @ u_el[1::2]
                        dv_dy = dNdx[1, :] @ u_el[1::2]
                        F_def = np.array([[1.0 + du_dx, du_dy], [dv_dx, 1.0 + du_dy]])
                        
                        E_GL = 0.5 * (F_def.T @ F_def - np.eye(2))
                        eps_vec = np.array([E_GL[0, 0], E_GL[1, 1], 2.0 * E_GL_0[0, 1]])
                        S_vec = self.C @ eps_vec
                        S_mat = np.array([[S_vec[0], S_vec[2]], [S_vec[2], S_vec[1]]])
                        
                        B = np.zeros((3, 8))
                        for a in range(4):
                            B[0, 2*a]     = F_def[0, 0] * dNdx[0, a]
                            B[0, 2*a + 1] = F_def[1, 0] * dNdx[0, a]
                            B[1, 2*a]     = F_def[0, 1] * dNdx[1, a]
                            B[1, 2*a + 1] = F_def[1, 1] * dNdx[1, a]
                            B[2, 2*a]     = F0[0, 0] * dNdx_0[1, a] + F0[0, 1] * dNdx_0[0, a]
                            B[2, 2*a + 1] = F0[1, 0] * dNdx_0[1, a] + F0[1, 1] * dNdx_0[0, a]
                            
                        dV = detJ * wt * self.depth
                        f_int[el_dofs] += B.T @ S_vec * dV
                        K_mat = B.T @ self.C @ B * dV
                        
                        G = np.zeros((4, 8))
                        for a in range(4):
                            G[0, 2*a] = dNdx[0, a]; G[1, 2*a] = dNdx[1, a]
                            G[2, 2*a+1] = dNdx[0, a]; G[3, 2*a+1] = dNdx[1, a]
                        M_S = np.block([[S_mat, np.zeros((2, 2))], [np.zeros((2, 2)), S_mat]])
                        K_geo = G.T @ M_S @ G * dV
                        K_tan[np.ix_(el_dofs, el_dofs)] += K_mat + K_geo
                        
                # Rigid constraints for S0 (intermediate shuttle)
                for sn in s0_nodes:
                    if sn == master_s0: continue
                    dx_diff = u[2*sn] - u[2*master_s0]
                    dy_diff = u[2*sn + 1] - u[2*master_s0 + 1]
                    f_int[2*sn] += k_rigid * dx_diff; f_int[2*master_s0] -= k_rigid * dx_diff
                    f_int[2*sn + 1] += k_rigid * dy_diff; f_int[2*master_s0 + 1] -= k_rigid * dy_diff
                    K_tan[2*sn, 2*sn] += k_rigid; K_tan[2*master_s0, 2*master_s0] += k_rigid
                    K_tan[2*sn, 2*master_s0] -= k_rigid; K_tan[2*master_s0, 2*sn] -= k_rigid
                    K_tan[2*sn + 1, 2*sn + 1] += k_rigid; K_tan[2*master_s0 + 1, 2*master_s0 + 1] += k_rigid
                    K_tan[2*sn + 1, 2*master_s0 + 1] -= k_rigid; K_tan[2*master_s0 + 1, 2*sn + 1] -= k_rigid
                    
                # Rigid constraints for S1 (output stage)
                for sn in s1_nodes:
                    if sn == master_s1: continue
                    dx_diff = u[2*sn] - u[2*master_s1]
                    dy_diff = u[2*sn + 1] - u[2*master_s1 + 1]
                    f_int[2*sn] += k_rigid * dx_diff; f_int[2*master_s1] -= k_rigid * dx_diff
                    f_int[2*sn + 1] += k_rigid * dy_diff; f_int[2*master_s1 + 1] -= k_rigid * dy_diff
                    K_tan[2*sn, 2*sn] += k_rigid; K_tan[2*master_s1, 2*master_s1] += k_rigid
                    K_tan[2*sn, 2*master_s1] -= k_rigid; K_tan[2*master_s1, 2*sn] -= k_rigid
                    K_tan[2*sn + 1, 2*sn + 1] += k_rigid; K_tan[2*master_s1 + 1, 2*master_s1 + 1] += k_rigid
                    K_tan[2*sn + 1, 2*master_s1 + 1] -= k_rigid; K_tan[2*master_s1 + 1, 2*sn + 1] -= k_rigid
                    
                res = f_curr - f_int
                if np.linalg.norm(res[free_dofs]) < 1e-4:
                    break
                u[free_dofs] += np.linalg.solve(K_tan[np.ix_(free_dofs, free_dofs)], res[free_dofs])
                
        dy_out_mm = float(u[2 * master_s1 + 1] * 1000.0)
        dx_out_mm = float(u[2 * master_s1] * 1000.0)
        return dy_out_mm, dx_out_mm

if __name__ == "__main__":
    print("Testing Dedicated Folded Shuttle 2D Continuum Solver...")
    solver = DedicatedFoldedShuttleContinuumSolver()
    t0 = time.time()
    dy_cont, dx_cont = solver.solve_continuum_mesh(F_trans=2.5, nx1=12, nx2=8, ny=2, n_steps=6)
    print(f"Continuum Result: dy = {dy_cont:.4f} mm, dx = {dx_cont:.4f} mm (Time: {time.time()-t0:.2f}s)")

"""P0 Deterministic Search: Symmetrically Balanced Double-Folded Parallelogram Stage."""

import numpy as np
from compliant_solver import CompliantFrameSolver

def build_symmetric_folded(L_outer, L_inner, y0, y1, y2, y3, h_beam, h_rigid=0.006, n_elem_per_beam=12):
    X_c = 0.045
    X_sL = X_c - L_inner
    X_aL = X_sL - L_outer
    X_sR = X_c + L_inner
    X_aR = X_sR + L_outer

    nodes = []
    elements = []
    widths = []

    def add_beam(x_start, y_start, x_end, y_end):
        nonlocal nodes, elements, widths
        n_start_idx = len(nodes)
        x_pts = np.linspace(x_start, x_end, n_elem_per_beam + 1)
        y_pts = np.linspace(y_start, y_end, n_elem_per_beam + 1)
        for i in range(n_elem_per_beam + 1):
            nodes.append([x_pts[i], y_pts[i]])
        for i in range(n_elem_per_beam):
            elements.append([n_start_idx + i, n_start_idx + i + 1])
            widths.append(h_beam)
        return n_start_idx, len(nodes) - 1

    b_oL_bot_s, b_oL_bot_e = add_beam(X_aL, y0, X_sL, y0)
    b_oL_top_s, b_oL_top_e = add_beam(X_aL, y3, X_sL, y3)
    b_iL_bot_s, b_iL_bot_e = add_beam(X_sL, y1, X_c, y1)
    b_iL_top_s, b_iL_top_e = add_beam(X_sL, y2, X_c, y2)

    b_oR_bot_s, b_oR_bot_e = add_beam(X_aR, y0, X_sR, y0)
    b_oR_top_s, b_oR_top_e = add_beam(X_aR, y3, X_sR, y3)
    b_iR_bot_s, b_iR_bot_e = add_beam(X_sR, y1, X_c, y1)
    b_iR_top_s, b_iR_top_e = add_beam(X_sR, y2, X_c, y2)

    elements.append([b_oL_bot_e, b_iL_bot_s]); widths.append(h_rigid)
    elements.append([b_iL_bot_s, b_iL_top_s]); widths.append(h_rigid)
    elements.append([b_iL_top_s, b_oL_top_e]); widths.append(h_rigid)

    elements.append([b_oR_bot_e, b_iR_bot_s]); widths.append(h_rigid)
    elements.append([b_iR_bot_s, b_iR_top_s]); widths.append(h_rigid)
    elements.append([b_iR_top_s, b_oR_top_e]); widths.append(h_rigid)

    y_mid = 0.5 * (y1 + y2)
    idx_out_mid = len(nodes)
    nodes.append([X_c, y_mid])
    elements.append([b_iL_bot_e, idx_out_mid]); widths.append(h_rigid)
    elements.append([b_iL_top_e, idx_out_mid]); widths.append(h_rigid)
    elements.append([b_iR_bot_e, idx_out_mid]); widths.append(h_rigid)
    elements.append([b_iR_top_e, idx_out_mid]); widths.append(h_rigid)

    nodes = np.array(nodes)
    elements = np.array(elements)
    widths = np.array(widths)

    ground_nodes = [b_oL_bot_s, b_oL_top_s, b_oR_bot_s, b_oR_top_s]
    boundary_dofs = {3 * gn + d: 0.0 for gn in ground_nodes for d in range(3)}
    forces = np.zeros(3 * len(nodes))
    forces[3 * idx_out_mid + 1] = 5.0
    return nodes, elements, widths, boundary_dofs, forces, idx_out_mid

def main():
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)

    print("=== P0 SEARCH: SYMMETRIC BALANCED DOUBLE-FOLDED PARALLEL STAGE ===")
    print("Testing parameters with STRICT bounds: Envelope [90x55]mm, h >= 0.60mm, F_y = 5.0N")
    print("-" * 90)

    for Lo in [0.021, 0.0215, 0.022]:
        for Li in [0.022, 0.0225]:
            for h in [0.00060, 0.00062]:
                nodes, elements, widths, b_dofs, forces, idx_mid = build_symmetric_folded(
                    Lo, Li, 0.008, 0.018, 0.034, 0.044, h, n_elem_per_beam=12
                )
                res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, b_dofs, forces, num_steps=10, tol=1e-6)
                u = res['displacements']
                dy = float(u[3*idx_mid+1])*1000
                dx = float(u[3*idx_mid])*1000
                th = float(np.degrees(abs(u[3*idx_mid+2])))
                s = res['max_stress_MPa']
                c_all = (dy >= 3.0 and s <= 25.0 and th <= 0.05 and abs(dx) <= 0.20 and h >= 0.00060)
                print(f"Lo={Lo*1000:.1f}mm Li={Li*1000:.1f}mm h={h*1000:.2f}mm | dy={dy:.4f}mm s={s:.2f}MPa th={th:.5f}deg dx={dx:.5f}mm | STRICT PASS: {c_all}")

if __name__ == "__main__":
    main()

import json
import numpy as np
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

def full_independent_audit(fixture_path, label):
    print(f"\n{'='*75}\nAUDIT: {label} ({fixture_path})\n{'='*75}")
    with open(fixture_path) as f:
        spec = json.load(f)

    # 1. Geometry & boundary checks
    anchors = spec["anchors"]
    stages = spec["stages"]
    conns = spec["connections"]
    out_idx = spec["output_stage"]

    print(f"Topology Name: {spec.get('topology_name')}")
    print(f"Stages: {len(stages)}, Anchors: {len(anchors)}, Connections: {len(conns)}")
    
    # Check bounding box
    all_x = [a[0] for a in anchors]
    all_y = [a[1] for a in anchors]
    for s in stages:
        cx, cy = s["center"]
        h = s["height"]
        all_x.append(cx)
        all_y.extend([cy - h/2.0, cy + h/2.0])

    print(f"Bounding Box: X in [{min(all_x)*1000:.2f}, {max(all_x)*1000:.2f}] mm, Y in [{min(all_y)*1000:.2f}, {max(all_y)*1000:.2f}] mm")
    env_ok = (min(all_x) >= -1e-6 and max(all_x) <= 0.090001 and min(all_y) >= -1e-6 and max(all_y) <= 0.055001)
    print(f"  Envelope [0-90mm, 0-55mm] satisfied: {env_ok}")

    # Check thickness
    thicknesses = [c["thickness"] for c in conns]
    min_t = min(thicknesses)
    thick_ok = min_t >= 0.0006000 - 1e-9
    print(f"Thicknesses (mm): {[round(t*1000, 4) for t in thicknesses]}")
    print(f"  Min thickness >= 0.600000 mm: {thick_ok} (min={min_t*1000:.6f} mm)")

    # 2. Compile at various N
    compiler = HardenedCompactCompiler()
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)

    for N in [12, 24, 36, 48, 64]:
        mesh = compiler.compile(spec, n_elem_per_beam=N)
        nodes = mesh["nodes"]
        elements = mesh["elements"]
        widths = mesh["widths"]
        ground_nodes = mesh["ground_nodes"]
        out_node = mesh["output_node"]

        b_dofs = {3 * g + d: 0.0 for g in ground_nodes for d in range(3)}
        forces = np.zeros(3 * len(nodes))
        forces[3 * out_node + 1] = 5.0

        num_steps = 10 if N <= 48 else 20
        try:
            res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, b_dofs, forces, num_steps=num_steps, tol=1e-6)
            u = res["displacements"]
            dy = u[3 * out_node + 1] * 1000.0
            dx = u[3 * out_node] * 1000.0
            th = np.degrees(u[3 * out_node + 2])
            sig = res["max_stress_MPa"]
            vol = res["volume_m3"] * 1e9

            pass_dy = dy >= 3.000000
            pass_sig = sig <= 25.000000
            pass_dx = abs(dx) <= 0.200000
            pass_th = abs(th) <= 0.050000
            overall = pass_dy and pass_sig and pass_dx and pass_th and thick_ok and env_ok

            print(f"  N={N:2d} ({len(elements):3d} elem): dy={dy:.6f} mm | sig={sig:.3f} MPa | dx={dx:.6f} mm | th={th:.6f} deg | Feasible: {overall}")
        except Exception as e:
            print(f"  N={N:2d}: SOLVER FAILED: {e}")

if __name__ == "__main__":
    full_independent_audit("muse_exp01_a_feasible_fixture.json", "exp_01_A (Compact)")
    full_independent_audit("muse_exp02_d_feasible_fixture.json", "exp_02_D (High Stroke)")
    full_independent_audit("p0_double_folded_fixture.json", "P0 Double-Folded (Ground Truth Reference)")

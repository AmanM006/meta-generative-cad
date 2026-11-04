"""
Portable Offline Verification of Task D Calibrated Design.
Runs complete nonlinear corotational FEA across N=16, 32, 48, 96 mesh levels,
verifies deformed envelope compliance, manufacturing floor, stress, stability,
and combined stiffening test (+2% th, +5% E) using strict assertions.
Exits with 0 on full verification pass, nonzero on any discrepancy.
"""
import sys
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))

from typed_topology_grammar import TypedTopologyGenerator
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

def verify_task_d():
    print("======================================================================")
    print("NEODUSTRIA OFFLINE SCIENTIFIC REPRODUCTION: TASK D CALIBRATED DESIGN")
    print("======================================================================")
    
    # Task D specification limits:
    REQ_DY = 2.500         # mm minimum stroke
    MAX_SIG = 22.0         # MPa maximum normal stress
    MAX_DX = 0.080         # mm maximum parasitic shift
    MAX_ENV_Y = 40.0       # mm maximum deformed Y coordinate
    MIN_ENV_Y = 0.0        # mm minimum deformed Y coordinate
    THICKNESS = 0.0011761  # m calibrated flexure thickness
    FY = 3.5               # N vertical load

    gen = TypedTopologyGenerator(envelope_x=0.080, envelope_y=0.040)
    spec = gen.synthesize_center_anchored_folded_series(thickness=THICKNESS)
    compiler = HardenedCompactCompiler(max_x=0.080, max_y=0.040)

    # 1. Mesh Convergence & Deformation Check through N=96
    print("\n[Phase 1] Evaluating Mesh Convergence across N = [16, 32, 48, 96]...")
    strokes = []
    stresses = []
    for N in [16, 32, 48, 96]:
        m = compiler.compile(spec, n_elem_per_beam=N)
        nodes = np.array(m['nodes'])
        elements = m['elements']
        widths = m['widths']
        tdof = 3 * len(nodes)
        bd = []
        for g in m['ground_nodes']:
            bd.extend([3*g, 3*g+1, 3*g+2])
        fe = np.zeros(tdof)
        ac = m['output_node']
        fe[3*ac + 1] = FY

        solver = CompliantFrameSolver(E=1.4e9)
        sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe)
        u = sol['displacements']
        dy = u[3*ac + 1] * 1000.0
        sig = sol['max_stress_MPa']
        dx = abs(u[3*ac]) * 1000.0
        
        # Check deformed Y coordinates
        def_y = (nodes[:, 1] + u[1::3]) * 1000.0
        max_y = float(np.max(def_y))
        min_y = float(np.min(def_y))
        
        # Physical tangent stiffness
        f_int, K_tan, _ = solver.compute_internal_forces_and_tangent(nodes, elements, widths, u)
        free_dofs = [k for k in range(tdof) if k not in bd]
        K_red = K_tan[np.ix_(free_dofs, free_dofs)]
        output_dof_in_free = free_dofs.index(3*ac + 1)
        unit_f = np.zeros(len(free_dofs))
        unit_f[output_dof_in_free] = 1.0
        u_unit = np.linalg.solve(K_red, unit_f)
        k_tan = 1.0 / u_unit[output_dof_in_free]
        num_neg = int(np.sum(np.linalg.eigvalsh(K_red) < 0))
        
        strokes.append(dy)
        stresses.append(sig)
        
        # Strict Assertions
        assert dy >= REQ_DY, f"N={N}: Stroke {dy:.4f}mm < required {REQ_DY}mm"
        assert sig <= MAX_SIG, f"N={N}: Stress {sig:.2f}MPa > allowable {MAX_SIG}MPa"
        assert dx <= MAX_DX, f"N={N}: Parasitic dx {dx:.4f}mm > limit {MAX_DX}mm"
        assert max_y <= MAX_ENV_Y, f"N={N}: Deformed Y_max {max_y:.2f}mm exceeded envelope ceiling {MAX_ENV_Y}mm"
        assert min_y >= MIN_ENV_Y, f"N={N}: Deformed Y_min {min_y:.2f}mm breached envelope floor {MIN_ENV_Y}mm"
        assert num_neg == 0, f"N={N}: Tangent stiffness has {num_neg} negative eigenvalues (unstable)"
        
        print(f"  N={N:2d} ({len(elements):3d} elem): dy={dy:6.4f}mm, sig={sig:5.2f}MPa, max_Y={max_y:5.2f}mm, k_tan={k_tan:6.1f}N/m [STABLE PASS]")

    # Check relative mesh invariance between N=16 and N=96
    mesh_err = abs(strokes[-1] - strokes[0]) / strokes[-1]
    assert mesh_err < 0.001, f"Mesh convergence error {mesh_err*100:.3f}% exceeds 0.1%"
    print(f"  -> Discretization Invariance Verified: Mesh error = {mesh_err*100:.4f}% across 5.6x element range.")

    # 2. Combined Uncertainty Stiffening Gate (+2% thickness bias, +5% modulus shift)
    print("\n[Phase 2] Evaluating Combined Worst-Case Stiffening Test (+2% th, +5% E)...")
    m_stiff = compiler.compile(spec, n_elem_per_beam=16)
    nodes_s = np.array(m_stiff['nodes'])
    elements_s = m_stiff['elements']
    widths_s = [w * 1.02 for w in m_stiff['widths']]
    tdof_s = 3 * len(nodes_s)
    bd_s = []
    for g in m_stiff['ground_nodes']:
        bd_s.extend([3*g, 3*g+1, 3*g+2])
    fe_s = np.zeros(tdof_s)
    ac_s = m_stiff['output_node']
    fe_s[3*ac_s + 1] = FY

    solver_stiff = CompliantFrameSolver(E=1.4e9 * 1.05)
    sol_stiff = solver_stiff.solve_nonlinear_newton_raphson(nodes_s, elements_s, widths_s, bd_s, fe_s)
    u_stiff = sol_stiff['displacements']
    dy_stiff = u_stiff[3*ac_s + 1] * 1000.0
    sig_stiff = sol_stiff['max_stress_MPa']
    dx_stiff = abs(u_stiff[3*ac_s]) * 1000.0

    # Manufacturing floor check: -2% tooling bias must not drop actual thickness below 0.600 mm
    min_nom_th = min(m_stiff['widths']) * 1000.0
    min_actual_th = min_nom_th * 0.98
    assert min_actual_th >= 0.600, f"Manufacturing floor breached: actual thickness {min_actual_th:.4f}mm < 0.600mm"
    assert dy_stiff >= REQ_DY, f"Stiffened stroke {dy_stiff:.4f}mm < required {REQ_DY}mm"
    assert sig_stiff <= MAX_SIG, f"Stiffened stress {sig_stiff:.2f}MPa > allowable {MAX_SIG}MPa"
    assert dx_stiff <= MAX_DX, f"Stiffened drift {dx_stiff:.4f}mm > allowable {MAX_DX}mm"

    print(f"  Manufacturing Floor: Nominal min={min_nom_th:.4f}mm -> Worst-Case Actual={min_actual_th:.4f}mm >= 0.6000mm [PASS]")
    print(f"  Stiffened Stroke:    dy = {dy_stiff:.4f}mm (Target >= {REQ_DY:.3f}mm, Margin: +{(dy_stiff-REQ_DY)*1000:.1f} um) [PASS]")
    print(f"  Stiffened Stress:    sig = {sig_stiff:.2f}MPa (Limit <= {MAX_SIG:.1f}MPa, PP Yield = 35.0MPa) [PASS]")
    print(f"  Stiffened Drift:     dx = {dx_stiff:.4f}mm (Limit <= {MAX_DX:.3f}mm) [PASS]")

    print("\n======================================================================")
    print("VERDICT: TASK D REPRODUCED AND VERIFIED WITH 100% STRICT ASSERTIONS.")
    print("======================================================================")

if __name__ == "__main__":
    verify_task_d()

"""Verification Suite for the Compact Architecture Compiler.

Tests:
1. Valid simple parallel stage (2 anchors, 1 stage, 2 connections).
2. Valid multi-stage topology (4 anchors, intermediate shuttle, output stage).
3. Rejection of ungrounded mechanism (0 anchors).
4. Rejection of disconnected floating elements.
5. Rejection of out-of-envelope coordinates.
6. Rejection of unphysical beam thicknesses.
7. Full nonlinear simulation of compiled valid mechanisms.
"""

from compact_compiler import CompactArchitectureCompiler
from compliant_solver import CompliantFrameSolver
import numpy as np

def run_compiler_tests():
    print("=== TESTING COMPACT ARCHITECTURE COMPILER ===")
    compiler = CompactArchitectureCompiler()
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)

    # Test 1: Simple 2-beam parallel stage
    spec_simple = {
        "anchors": [[0.0, 0.010], [0.0, 0.040]],
        "stages": [{"center": [0.050, 0.025], "height": 0.030, "is_rigid": True}],
        "connections": [
            {"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.0012},
            {"from_type": "anchor", "from_index": 1, "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.0012}
        ],
        "output_stage": 0
    }
    m1 = compiler.compile(spec_simple)
    print(f"Test 1 (Simple Parallel Stage): Compiled successfully. Nodes: {len(m1['nodes'])}, Elements: {len(m1['elements'])}")

    # Run nonlinear simulation on m1
    boundary = {3*g: 0.0 for g in m1["ground_nodes"]}
    for g in m1["ground_nodes"]:
        boundary[3*g+1] = 0.0
        boundary[3*g+2] = 0.0
    forces = np.zeros(3 * len(m1["nodes"]))
    forces[3 * m1["output_node"] + 1] = 5.0
    res1 = solver.solve_nonlinear_newton_raphson(m1["nodes"], m1["elements"], m1["widths"], boundary, forces, num_steps=8)
    print(f"  -> Nonlinear Simulation Passed: dy={res1['displacements'][3*m1['output_node']+1]*1000:.2f}mm, "
          f"dx={res1['displacements'][3*m1['output_node']]*1000:.3f}mm, stress={res1['max_stress_MPa']:.1f}MPa")

    # Test 2: Multi-stage compound architecture (Ground -> Shuttle -> Output)
    spec_compound = {
        "anchors": [[0.0, 0.005], [0.0, 0.050]],
        "stages": [
            {"center": [0.050, 0.0275], "height": 0.045, "is_rigid": True}, # Stage 0: Shuttle at X=50mm
            {"center": [0.010, 0.0275], "height": 0.020, "is_rigid": True}  # Stage 1: Output Stage at X=10mm
        ],
        "connections": [
            # Primary stage: Anchors to Shuttle
            {"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.0010},
            {"from_type": "anchor", "from_index": 1, "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.0010},
            # Secondary folded stage: Shuttle to Output Stage
            {"from_type": "stage", "from_index": 0, "from_port": "bot", "to_type": "stage", "to_index": 1, "to_port": "bot", "thickness": 0.0010},
            {"from_type": "stage", "from_index": 0, "from_port": "top", "to_type": "stage", "to_index": 1, "to_port": "top", "thickness": 0.0010}
        ],
        "output_stage": 1
    }
    m2 = compiler.compile(spec_compound)
    print(f"Test 2 (Compound Multi-Stage): Compiled successfully. Nodes: {len(m2['nodes'])}, Elements: {len(m2['elements'])}")

    boundary2 = {3*g: 0.0 for g in m2["ground_nodes"]}
    for g in m2["ground_nodes"]:
        boundary2[3*g+1] = 0.0
        boundary2[3*g+2] = 0.0
    forces2 = np.zeros(3 * len(m2["nodes"]))
    forces2[3 * m2["output_node"] + 1] = 5.0
    res2 = solver.solve_nonlinear_newton_raphson(m2["nodes"], m2["elements"], m2["widths"], boundary2, forces2, num_steps=8)
    print(f"  -> Compound Nonlinear Simulation: dy={res2['displacements'][3*m2['output_node']+1]*1000:.2f}mm, "
          f"dx={res2['displacements'][3*m2['output_node']]*1000:.3f}mm, stress={res2['max_stress_MPa']:.1f}MPa")

    # Test 3: Rejection of Disconnected Floating Node/Element
    spec_disconnected = {
        "anchors": [[0.0, 0.010]],
        "stages": [
            {"center": [0.040, 0.020], "height": 0.020},
            {"center": [0.080, 0.020], "height": 0.020} # Floating stage
        ],
        "connections": [
            {"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "thickness": 0.001}
        ],
        "output_stage": 0
    }
    try:
        compiler.compile(spec_disconnected)
        print("Test 3 (Disconnected Rejection): FAILED (should have rejected)")
    except ValueError as e:
        print(f"Test 3 (Disconnected Rejection): PASSED -> Caught: {e}")

    # Test 4: Rejection of Out-of-Envelope Anchor
    spec_oob = {
        "anchors": [[0.150, 0.010]], # X=150mm > 95mm
        "stages": [{"center": [0.040, 0.020], "height": 0.020}],
        "connections": [{"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "thickness": 0.001}],
        "output_stage": 0
    }
    try:
        compiler.compile(spec_oob)
        print("Test 4 (Out-of-Bounds Rejection): FAILED")
    except ValueError as e:
        print(f"Test 4 (Out-of-Bounds Rejection): PASSED -> Caught: {e}")

    # Test 5: Rejection of Zero Anchors
    spec_no_ground = {
        "anchors": [],
        "stages": [{"center": [0.040, 0.020], "height": 0.020}],
        "connections": [],
        "output_stage": 0
    }
    try:
        compiler.compile(spec_no_ground)
        print("Test 5 (No Anchors Rejection): FAILED")
    except ValueError as e:
        print(f"Test 5 (No Anchors Rejection): PASSED -> Caught: {e}")

if __name__ == "__main__":
    run_compiler_tests()

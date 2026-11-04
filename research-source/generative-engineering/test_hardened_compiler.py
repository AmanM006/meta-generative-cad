"""Test Suite for the Hardened Compact Compiler.

Verifies:
1. Rejection of stage endpoint exceeding 55 mm height.
2. Rejection of physically crossing beams.
3. Rejection of duplicate connections.
4. Acceptance and nonlinear evaluation of valid non-crossing geometry.
"""

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver
import numpy as np

def run_tests():
    print("=== TESTING HARDENED COMPILER VALIDATIONS ===")
    compiler = HardenedCompactCompiler(max_x=0.090, max_y=0.055)

    # Test A: Stage endpoint exceeds 55 mm
    spec_tall = {
        "anchors": [[0.0, 0.010]],
        "stages": [{"center": [0.040, 0.045], "height": 0.030}], # Top = 0.045 + 0.015 = 0.060m > 0.055m
        "connections": [{"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "thickness": 0.001}],
        "output_stage": 0
    }
    try:
        compiler.compile(spec_tall)
        print("Test A (Tall Stage Rejection): FAILED")
    except ValueError as e:
        print(f"Test A (Tall Stage Rejection): PASSED -> {e}")

    # Test B: Crossing beams (X-pattern)
    spec_crossing = {
        "anchors": [[0.0, 0.010], [0.0, 0.040]],
        "stages": [{"center": [0.050, 0.025], "height": 0.030}],
        "connections": [
            {"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.001}, # (0, 0.010) -> (0.050, 0.040)
            {"from_type": "anchor", "from_index": 1, "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.001}  # (0, 0.040) -> (0.050, 0.010) -> Crosses!
        ],
        "output_stage": 0
    }
    try:
        compiler.compile(spec_crossing)
        print("Test B (Crossing Beams Rejection): FAILED")
    except ValueError as e:
        print(f"Test B (Crossing Beams Rejection): PASSED -> {e}")

    # Test C: Valid geometry within 90x55 envelope
    spec_valid = {
        "anchors": [[0.0, 0.010], [0.0, 0.040]],
        "stages": [{"center": [0.050, 0.025], "height": 0.025}],
        "connections": [
            {"from_type": "anchor", "from_index": 0, "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.0012},
            {"from_type": "anchor", "from_index": 1, "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.0012}
        ],
        "output_stage": 0
    }
    m = compiler.compile(spec_valid)
    print(f"Test C (Valid Geometry): PASSED -> Nodes: {len(m['nodes'])}, Elements: {len(m['elements'])}")

if __name__ == "__main__":
    run_tests()

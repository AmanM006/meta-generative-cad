"""
Portable, Strict Assertion Test Suite for Typed Topology Grammar & Compiler.
Exits with nonzero exit code on any failure. No hardcoded absolute paths.
"""
import sys
from pathlib import Path

# Portable import relative to current test script
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))

from typed_topology_grammar import TypedTopologyGenerator
from hardened_compiler import HardenedCompactCompiler

def test_nominal_synthesis():
    gen = TypedTopologyGenerator(envelope_x=0.080, envelope_y=0.040)
    spec = gen.synthesize_center_anchored_folded_series(thickness=0.000725)
    compiler = HardenedCompactCompiler(max_x=0.080, max_y=0.040)
    m = compiler.compile(spec, n_elem_per_beam=8)
    
    assert len(m["nodes"]) == 71, f"Expected 71 nodes, got {len(m['nodes'])}"
    assert len(m["elements"]) == 74, f"Expected 74 elements, got {len(m['elements'])}"
    assert len(m["ground_nodes"]) == 2, f"Expected 2 ground nodes, got {len(m['ground_nodes'])}"
    assert m["output_node"] == 13, f"Expected output node 13, got {m['output_node']}"
    print("[PASS] test_nominal_synthesis")

def test_stage_port_geometry_consistency():
    gen = TypedTopologyGenerator(envelope_x=0.080, envelope_y=0.040)
    spec = gen.synthesize_center_anchored_folded_series(thickness=0.000725)
    
    for i, s in enumerate(spec["stages"]):
        c = s["center"]
        h = s["height"]
        for pname, ppos in s["ports"].items():
            dy = abs(ppos[1] - c[1])
            assert dy <= (h / 2.0 + 1e-6), (
                f"Stage {i} port {pname} at y={ppos[1]} is outside stage height bounds "
                f"[c_y - h/2, c_y + h/2] = [{c[1]-h/2}, {c[1]+h/2}]"
            )
    print("[PASS] test_stage_port_geometry_consistency")

def test_boundary_guards():
    # 1. Margin too large for envelope height
    try:
        TypedTopologyGenerator(envelope_x=0.080, envelope_y=0.040, margin=0.025)
        assert False, "Failed to reject margin >= envelope_y / 2"
    except ValueError:
        pass

    # 2. Margin too large for envelope width
    try:
        TypedTopologyGenerator(envelope_x=0.080, envelope_y=0.040, margin=0.045)
        assert False, "Failed to reject margin >= envelope_x / 2"
    except ValueError:
        pass
    print("[PASS] test_boundary_guards")

def test_thick_and_narrow_parameters():
    gen = TypedTopologyGenerator(envelope_x=0.080, envelope_y=0.040)
    compiler = HardenedCompactCompiler(max_x=0.080, max_y=0.040)
    
    # Thick rigids
    spec_thick = gen.synthesize_center_anchored_folded_series(thickness=0.0012, shuttle_width=0.005)
    m_thick = compiler.compile(spec_thick, n_elem_per_beam=8)
    assert len(m_thick["nodes"]) > 0
    
    # Narrow shuttles
    spec_narrow = gen.synthesize_center_anchored_folded_series(thickness=0.00065, shuttle_width=0.002)
    m_narrow = compiler.compile(spec_narrow, n_elem_per_beam=8)
    assert len(m_narrow["nodes"]) > 0
    print("[PASS] test_thick_and_narrow_parameters")

if __name__ == "__main__":
    print("Running portable test suite...")
    test_nominal_synthesis()
    test_stage_port_geometry_consistency()
    test_boundary_guards()
    test_thick_and_narrow_parameters()
    print("ALL TESTS PASSED WITH STRICT ASSERTIONS.")

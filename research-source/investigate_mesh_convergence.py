"""
Investigate mesh convergence on tapered flexure across N = 8, 16, 32, 64, 96 elements per beam
using correct connection-aware beam element tapering.
"""

import sys
import json
import time
import numpy as np
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))
sys.path.insert(0, str(BASE_DIR / "generative_engineering_src"))

from typed_topology_grammar import TypedTopologyGenerator
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver
from beam_taper_compiler import compile_with_beam_metadata, apply_taper_to_beam_elements

# Task O specs: 90x35 mm, Fy = 4.5 N
env_x, env_y = 0.090, 0.035
Fy = 4.5
gen = TypedTopologyGenerator(env_x, env_y)
comp = HardenedCompactCompiler(env_x, env_y)
solver = CompliantFrameSolver(E=1.4e9)

spec = gen.synthesize_by_name("bilateral_compound_parallelogram")
nominal_th = 0.00095 # ensures minimum thickness >= 0.600 mm even with 0.70 taper! (0.00095 * 0.70 = 0.000665 m)
for c in spec["connections"]: c["thickness"] = nominal_th

taper_ratio = 0.75
n_sweep = [8, 16, 32, 64, 96]
results = []

print("Running Rigorous Mesh Convergence Sweep for Tapered Flexure...")

for n in n_sweep:
    t0 = time.time()
    mesh = compile_with_beam_metadata(comp, spec, n_elem_per_beam=n)
    mesh = apply_taper_to_beam_elements(mesh, spec, n_elem_per_beam=n, taper_ratio=taper_ratio)
    
    nodes = np.array(mesh["nodes"])
    elements = mesh["elements"]
    widths = mesh["widths"]
    
    tdof = 3 * len(nodes)
    bd = []
    for g in mesh["ground_nodes"]:
        bd.extend([3 * g, 3 * g + 1, 3 * g + 2])
    fe = np.zeros(tdof)
    ac = mesh["output_node"]
    fe[3 * ac + 1] = Fy
    
    sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths.tolist(), bd, fe)
    dy_mm = float(sol["displacements"][3 * ac + 1] * 1000.0)
    sig_mpa = float(sol["max_stress_MPa"])
    elapsed = time.time() - t0
    
    # Check minimum width
    min_w_mm = float(np.min(widths)) * 1000.0
    
    results.append({
        "n_elem_per_beam": n,
        "total_nodes": len(nodes),
        "total_elements": len(elements),
        "min_width_mm": round(min_w_mm, 4),
        "dy_mm": round(dy_mm, 5),
        "sig_mpa": round(sig_mpa, 2),
        "solve_time_s": round(elapsed, 4)
    })
    print(f"N={n:2d} elements | Nodes={len(nodes):4d} | Stroke={dy_mm:.5f} mm | Stress={sig_mpa:.2f} MPa | Min_w={min_w_mm:.3f} mm in {elapsed:.3f}s")

# Analyze convergence
dy_finest = results[-1]["dy_mm"]
for r in results:
    r["error_from_finest_pct"] = round(100.0 * abs(r["dy_mm"] - dy_finest) / dy_finest, 3)

# Check monotonicity
diffs = [results[i+1]["dy_mm"] - results[i]["dy_mm"] for i in range(len(results)-1)]
is_monotonic = all(d <= 1e-4 for d in diffs) or all(d >= -1e-4 for d in diffs)

print(f"\nDiscrepancy N=8 vs N=96: {results[0]['error_from_finest_pct']}%")
print(f"Discrepancy N=16 vs N=96: {results[1]['error_from_finest_pct']}%")
print(f"Discrepancy N=32 vs N=96: {results[2]['error_from_finest_pct']}%")
print(f"Discrepancy N=64 vs N=96: {results[3]['error_from_finest_pct']}%")
print(f"Monotonic Convergence Verified: {is_monotonic}")

with open("investigate_mesh_convergence.json", "w") as f:
    json.dump({
        "taper_ratio": taper_ratio,
        "nominal_thickness_mm": nominal_th * 1000.0,
        "is_monotonic": is_monotonic,
        "results": results
    }, f, indent=2)

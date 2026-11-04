"""
Phase 22: Generation of Frozen 30-Task Held-Out Physical Benchmark Suite
=======================================================================
Generates 30 systematically partitioned physical tasks spanning:
- Low (0.5 - 1.5 N), Medium (2.0 - 5.0 N), and High (6.0 - 15.0 N) forces
- Compact (35x35mm) to Wide (120x45mm) aspect-ratio envelopes
- Polypropylene (E=1.4 GPa), Delrin (E=2.8 GPa), and Titanium Ti-6Al-4V (E=110 GPa)
- High-stroke compliance vs ultra-strict absolute lateral drift (0.010 - 0.050 mm)
- Fixed ground truth for fair hybrid vs classical benchmarks.
"""

import json
from pathlib import Path

tasks = []

materials = [
    {"name": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)", "E": 1.4e9, "yield": 35.0},
    {"name": "Delrin POM (E=2.8 GPa, yield=65.0 MPa)", "E": 2.8e9, "yield": 65.0},
    {"name": "Titanium Ti-6Al-4V (E=110.0 GPa, yield=880.0 MPa)", "E": 110.0e9, "yield": 880.0}
]

# Systematic parameter combinations
configs = [
    # Low-force precision regime (Tasks 01 - 10)
    (0.5, 0.75, 0.020, [45, 45], 0, 14.0, "Micro-gripper flexure guide"),
    (0.8, 0.90, 0.025, [95, 55], 0, 14.0, "Low-force scanning probe stage"),
    (1.0, 1.10, 0.030, [60, 40], 0, 15.0, "Optical fiber alignment stage"),
    (0.6, 0.85, 0.015, [50, 50], 0, 12.0, "Ultra-low drift sensor guide"),
    (1.2, 1.25, 0.030, [70, 45], 0, 16.0, "Compact dual-axis flexure pivot"),
    (1.5, 1.40, 0.035, [80, 50], 0, 16.0, "Precision microscope fine-focus stage"),
    (0.7, 0.80, 0.020, [55, 35], 0, 14.0, "MEMS mirror actuation suspension"),
    (1.1, 1.05, 0.025, [65, 45], 0, 15.0, "Precision laser collimator mount"),
    (1.4, 1.30, 0.030, [75, 50], 0, 16.0, "Interferometer retroreflector flexure"),
    (0.9, 1.00, 0.020, [85, 40], 0, 15.0, "High-bandwidth galvanometer stage"),

    # Medium-force moderate stroke regime (Tasks 11 - 20)
    (2.0, 1.50, 0.035, [90, 50], 1, 28.0, "Delrin optical switch shuttle"),
    (2.5, 1.70, 0.040, [90, 35], 0, 18.0, "Task N frozen equivalent flexure"),
    (3.0, 1.80, 0.040, [85, 55], 1, 30.0, "Delrin precision linear bearing"),
    (3.5, 1.60, 0.035, [100, 50], 1, 32.0, "Long-travel compliant carriage"),
    (2.2, 1.45, 0.030, [70, 50], 0, 16.0, "High-stiffness precision positioning stage"),
    (4.0, 1.90, 0.045, [110, 55], 1, 35.0, "Delrin heavy-load optical platform"),
    (2.8, 1.55, 0.035, [95, 45], 0, 18.0, "Folded scanning flexure mechanism"),
    (3.2, 1.65, 0.040, [85, 50], 1, 30.0, "Modular robotic gripper compliant jaw"),
    (4.5, 2.00, 0.050, [115, 55], 1, 38.0, "Extended-reach compliant micro-positioner"),
    (2.4, 1.35, 0.030, [80, 45], 0, 16.0, "Cryogenic detector flexure suspension"),

    # High-force & extreme modulus regime (Tasks 21 - 30)
    (6.0, 1.80, 0.045, [95, 55], 1, 45.0, "High-load bistable switch latch"),
    (8.0, 2.10, 0.050, [95, 55], 0, 24.0, "Heavy-load breaker compliant transmission"),
    (10.0, 1.90, 0.045, [100, 60], 1, 50.0, "Delrin structural flexure hinge"),
    (12.0, 2.20, 0.050, [120, 65], 1, 55.0, "Heavy payload compliant decoupling mechanism"),
    (15.0, 0.35, 0.015, [60, 50], 2, 400.0, "Titanium aerospace cryogenic flexure"),
    (20.0, 0.28, 0.012, [55, 45], 2, 450.0, "Titanium high-frequency piezostage guide"),
    (25.0, 0.25, 0.010, [50, 40], 2, 450.0, "Titanium ultra-precision optical mount"),
    (18.0, 0.32, 0.015, [65, 50], 2, 420.0, "Titanium vibration-isolation flexure strut"),
    (7.5, 1.75, 0.040, [90, 50], 1, 48.0, "Industrial pick-and-place compliant wrist"),
    (11.0, 2.05, 0.050, [105, 55], 1, 52.0, "High-cycle fatigue compliant flexure joint")
]

for idx, (fy, dy, dx, env, mat_idx, sig_max, desc) in enumerate(configs):
    mat = materials[mat_idx]
    tasks.append({
        "task_id": f"Task_{idx+1:02d}",
        "task_name": f"Task {idx+1:02d}: {desc}",
        "Fy_N": fy,
        "req_stroke_mm": dy,
        "max_parasitic_dx_mm": dx,
        "max_stress_MPa": sig_max,
        "envelope_mm": env,
        "material": mat["name"],
        "material_E": mat["E"],
        "material_yield_MPa": mat["yield"]
    })

payload = {
    "title": "Neodustria Phase 22 Frozen 30-Task Held-Out Physical Benchmark Suite",
    "tasks_count": len(tasks),
    "benchmark_tasks": tasks
}

with open("BENCHMARK_30_HELD_OUT_TASKS.json", "w") as f:
    json.dump(payload, f, indent=2)

print(f"Successfully generated BENCHMARK_30_HELD_OUT_TASKS.json ({len(tasks)} tasks)!")

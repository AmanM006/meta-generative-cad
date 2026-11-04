"""
Preregistered Benchmark Definition for Held-Out Evaluation of CASM.
Task G: Balanced Precision Actuator (70x45mm, 4.0N, dy >= 1.800mm, sig <= 20.0MPa, |dx| <= 0.050mm)
Task H: High-Force Compact Inserter (60x40mm, 7.0N, dy >= 1.500mm, sig <= 22.0MPa, |dx| <= 0.050mm)
"""
import json, hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TASKS = {
    "Task G (Balanced Precision Actuator)": {
        "task_name": "Task G (Balanced Precision Actuator)",
        "envelope_mm": [70.0, 45.0],
        "Fy_N": 4.0,
        "req_stroke_mm": 1.800,
        "max_stress_MPa": 20.0,
        "max_parasitic_dx_mm": 0.050,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "description": "Moderate-force intermediate-scale precision stage requiring balanced compliance and lateral rigidity."
    },
    "Task H (High-Force Compact Inserter)": {
        "task_name": "Task H (High-Force Compact Inserter)",
        "envelope_mm": [60.0, 40.0],
        "Fy_N": 7.0,
        "req_stroke_mm": 1.500,
        "max_stress_MPa": 22.0,
        "max_parasitic_dx_mm": 0.050,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "description": "High-force compact stage testing the boundary where force is high (7.0N) but envelope width (60mm) is near minimum compound limits."
    }
}

manifest_path = BASE_DIR / "UNSEEN_HELD_OUT_BENCHMARK_GH.json"
content_bytes = json.dumps(TASKS, indent=2).encode('utf-8')
with open(manifest_path, "wb") as f:
    f.write(content_bytes)

sha256 = hashlib.sha256(content_bytes).hexdigest()
print(f"Preregistered Tasks G and H saved to {manifest_path.name}")
print(f"SHA-256 Checksum: {sha256}")

"""
Preregistered Frontier Scalability Benchmark Manifest.
Evaluates 8-topology mechanical discovery across four genuinely unseen engineering challenges:
- Task L (High-Force Heavy-Load Switch): 95x55mm, Fy=9.0N, dy >= 2.200mm, sig <= 25.0MPa, |dx| <= 0.050mm
- Task M (Compact Micro-Precision Stage): 50x35mm, Fy=1.0N, dy >= 1.200mm, sig <= 15.0MPa, |dx| <= 0.030mm
- Task N (Amplified Stroke Resonator): 70x40mm, Fy=2.5N, dy >= 1.700mm, sig <= 18.0MPa, |dx| <= 0.040mm
- Task O (Ultra-Wide High-Aspect Guide): 90x35mm, Fy=4.5N, dy >= 1.500mm, sig <= 20.0MPa, |dx| <= 0.040mm
"""
import json, hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TASKS = {
    "Task L (High-Force Heavy-Load Switch)": {
        "task_name": "Task L (High-Force Heavy-Load Switch)",
        "envelope_mm": [95.0, 55.0],
        "Fy_N": 9.0,
        "req_stroke_mm": 2.200,
        "max_stress_MPa": 25.0,
        "max_parasitic_dx_mm": 0.050,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "regime": "High force (9.0N) macro stage testing whether system rejects folded compliance saturation."
    },
    "Task M (Compact Micro-Precision Stage)": {
        "task_name": "Task M (Compact Micro-Precision Stage)",
        "envelope_mm": [50.0, 35.0],
        "Fy_N": 1.0,
        "req_stroke_mm": 1.200,
        "max_stress_MPa": 15.0,
        "max_parasitic_dx_mm": 0.030,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "regime": "Compact envelope (50x35mm) micro-force testing avoidance of over-stiff compound stages."
    },
    "Task N (Amplified Stroke Resonator)": {
        "task_name": "Task N (Amplified Stroke Resonator)",
        "envelope_mm": [70.0, 40.0],
        "Fy_N": 2.5,
        "req_stroke_mm": 1.700,
        "max_stress_MPa": 18.0,
        "max_parasitic_dx_mm": 0.040,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "regime": "Moderate force (2.5N) testing whether transmission/folded architectures achieve high stroke."
    },
    "Task O (Ultra-Wide High-Aspect Guide)": {
        "task_name": "Task O (Ultra-Wide High-Aspect Guide)",
        "envelope_mm": [90.0, 35.0],
        "Fy_N": 4.5,
        "req_stroke_mm": 1.500,
        "max_stress_MPa": 20.0,
        "max_parasitic_dx_mm": 0.040,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "regime": "Extreme aspect ratio (90x35mm, AR=2.57) testing packaging link clearance."
    }
}

manifest_path = BASE_DIR / "UNSEEN_HELD_OUT_BENCHMARK_LMNO.json"
content_bytes = json.dumps(TASKS, indent=2).encode('utf-8')
with open(manifest_path, "wb") as f:
    f.write(content_bytes)

sha256 = hashlib.sha256(content_bytes).hexdigest()
print(f"Preregistered Tasks L, M, N, O saved to {manifest_path.name}")
print(f"SHA-256 Checksum: {sha256}")

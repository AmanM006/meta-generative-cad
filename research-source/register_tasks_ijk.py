"""
Preregistered Benchmark Specification for CASM Causal Ablation.
Three unseen, untouched mechanical specifications spanning distinct physical regimes:
- Task I (Micro-Force Asymmetric Filter): 55x35mm, Fy=1.2N, dy >= 1.400mm, sig <= 16.0MPa, |dx| <= 0.040mm, |dtheta| <= 0.020deg
- Task J (Macro-Scale Industrial Switch): 85x50mm, Fy=6.5N, dy >= 2.000mm, sig <= 22.0MPa, |dx| <= 0.050mm, |dtheta| <= 0.020deg
- Task K (Boundary-Constrained High-AspectRatio Sorter): 75x35mm, Fy=3.8N, dy >= 1.600mm, sig <= 18.0MPa, |dx| <= 0.040mm, |dtheta| <= 0.020deg
"""
import json, hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TASKS = {
    "Task I (Micro-Force Precision Filter)": {
        "task_name": "Task I (Micro-Force Precision Filter)",
        "envelope_mm": [55.0, 35.0],
        "Fy_N": 1.2,
        "req_stroke_mm": 1.400,
        "max_stress_MPa": 16.0,
        "max_parasitic_dx_mm": 0.040,
        "max_parasitic_dtheta_deg": 0.020,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "description": "Low-force regime (1.2N) in compact envelope, testing whether system avoids over-stiff compound topology while maintaining 0.600mm floor."
    },
    "Task J (Macro-Scale Industrial Switch)": {
        "task_name": "Task J (Macro-Scale Industrial Switch)",
        "envelope_mm": [85.0, 50.0],
        "Fy_N": 6.5,
        "req_stroke_mm": 2.000,
        "max_stress_MPa": 22.0,
        "max_parasitic_dx_mm": 0.050,
        "max_parasitic_dtheta_deg": 0.020,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "description": "High-force regime (6.5N) in macro envelope, testing whether memory avoids compliance saturation of folded series."
    },
    "Task K (Boundary-Constrained Aspect Sorter)": {
        "task_name": "Task K (Boundary-Constrained Aspect Sorter)",
        "envelope_mm": [75.0, 35.0],
        "Fy_N": 3.8,
        "req_stroke_mm": 1.600,
        "max_stress_MPa": 18.0,
        "max_parasitic_dx_mm": 0.040,
        "max_parasitic_dtheta_deg": 0.020,
        "material": "Polypropylene (E=1.4 GPa, yield=35.0 MPa)",
        "min_actual_thickness_mm": 0.600000,
        "description": "High aspect-ratio regime (75x35mm) at 3.8N, testing intermediate boundary arbitration."
    }
}

manifest_path = BASE_DIR / "UNSEEN_HELD_OUT_BENCHMARK_IJK.json"
content_bytes = json.dumps(TASKS, indent=2).encode('utf-8')
with open(manifest_path, "wb") as f:
    f.write(content_bytes)

sha256 = hashlib.sha256(content_bytes).hexdigest()
print(f"Preregistered Tasks I, J, K saved to {manifest_path.name}")
print(f"SHA-256 Checksum: {sha256}")

import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

# Symmetrical 2-Anchor Parallel-Guided Series Shuttle
# Ground anchors: A0=[0.005, 0.035], A1=[0.005, 0.005]
# Stage 0 (Floating intermediate shuttle): center=[0.025, 0.020], height=0.030
# Stage 1 (Output shuttle): center=[0.055, 0.020], height=0.024
# Beams 1 & 2: A0->S0 top, A1->S0 bot. Length L1 = 0.020m.
# Beams 3 & 4: S0 top->S1 top, S0 bot->S1 bot. Length L2 = 0.030m.
# Notice L1 != L2! Since L1=20mm and L2=30mm, they foreshorten by different amounts:
# delta_x1 = - (dy1^2) / (2 * L1)
# delta_x2 = + (dy2^2) / (2 * L2)
# If L1 == L2 and they are oriented oppositely (folded), the foreshortenings cancel out to 0!
# Let's test a Folded Floating Shuttle:
# Anchors at x = 0.005 (top and bot)
# Intermediate Shuttle S0 at x = 0.055 (right side)
# Stage 1 (Output Shuttle) folds back to x = 0.025 (or vice versa)
env_x = 0.070
env_y = 0.040
margin = 0.005

anchors = [
    [margin, env_y - margin], # A0: [0.005, 0.035]
    [margin, margin]          # A1: [0.005, 0.005]
]

# S0: Right intermediate shuttle at x = 0.055, height = 0.030
# S1: Left output stage at x = 0.015, height = 0.020
stages = [
    {
        "center": [0.055, 0.020], "height": 0.030, "thickness": 0.003, "is_rigid": True,
        "ports": {"top": [0.055, 0.035], "bot": [0.055, 0.005], "mid_top": [0.055, 0.027], "mid_bot": [0.055, 0.013], "center": [0.055, 0.020]}
    },
    {
        "center": [0.020, 0.020], "height": 0.018, "thickness": 0.003, "is_rigid": True,
        "ports": {"top": [0.020, 0.029], "bot": [0.020, 0.011], "center": [0.020, 0.020]}
    }
]

# Beams:
# A0 -> S0 top (length 50mm)
# A1 -> S0 bot (length 50mm)
# S0 mid_top -> S1 top (length 35mm, folded back in -X direction!)
# S0 mid_bot -> S1 bot (length 35mm, folded back in -X direction!)
connections = [
    {"from_type": "anchor", "from_index": 0, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "top", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "anchor", "from_index": 1, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "bot", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "stage", "from_index": 0, "from_port": "mid_top", "to_type": "stage", "to_index": 1, "to_port": "top", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "stage", "from_index": 0, "from_port": "mid_bot", "to_type": "stage", "to_index": 1, "to_port": "bot", "is_tapered": True, "taper_ratio": 0.75}
]

spec = {
    "id": "NOVEL_COMPOSITION_FOLDED_FLOATING_SHUTTLE_TR75",
    "architecture_class": "folded_floating_shuttle",
    "output_stage": 1,
    "taper_ratio": 0.75,
    "anchors": anchors,
    "stages": stages,
    "connections": connections
}

eng = TopologyInnovationEngineV2(env_x=env_x, env_y=env_y)
for th in [0.00095, 0.00105, 0.00115, 0.00125]:
    res = eng.evaluate_task_specific(spec, th, 2.5, 1.70, 18.0)
    dy = res.get("stroke_dy_mm")
    dx = res.get("parasitic_dx_mm")
    sig = res.get("max_stress_MPa")
    feas = res.get("is_feasible")
    print(f"Folded Floating Shuttle th={th*1e3:.2f}mm -> dy={dy}, dx={dx}, sig={sig}, feas={feas}, reason={res.get('rejection_reason')}")

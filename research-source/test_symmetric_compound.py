import sys
from pathlib import Path
import copy
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2

# Let's test a symmetric bilateral double-stage flexure
# Left anchor pair at x = margin, right anchor pair at x = env_x - margin
# Intermediate shuttle left at x = 0.022, intermediate shuttle right at x = 0.048
# Central output stage at x = 0.035
env_x = 0.070
env_y = 0.040
margin = 0.005

anchors = [
    [margin, env_y - margin],         # A0: top-left [0.005, 0.035]
    [margin, margin],                 # A1: bot-left [0.005, 0.005]
    [env_x - margin, env_y - margin], # A2: top-right [0.065, 0.035]
    [env_x - margin, margin]          # A3: bot-right [0.065, 0.005]
]

# Stages:
# S0: Left floating shuttle at x = 0.022, y = 0.020
# S1: Right floating shuttle at x = 0.048, y = 0.020
# S2: Center output shuttle at x = 0.035, y = 0.020
stages = [
    {
        "center": [0.022, 0.020], "height": 0.028, "thickness": 0.0025, "is_rigid": True,
        "ports": {"top": [0.022, 0.034], "bot": [0.022, 0.006], "center": [0.022, 0.020]}
    },
    {
        "center": [0.048, 0.020], "height": 0.028, "thickness": 0.0025, "is_rigid": True,
        "ports": {"top": [0.048, 0.034], "bot": [0.048, 0.006], "center": [0.048, 0.020]}
    },
    {
        "center": [0.035, 0.020], "height": 0.022, "thickness": 0.003, "is_rigid": True,
        "ports": {"top": [0.035, 0.031], "bot": [0.035, 0.009], "center": [0.035, 0.020]}
    }
]

# Symmetrical load path:
# A0 -> S0 top, A1 -> S0 bot (left parallelogram)
# A2 -> S1 top, A3 -> S1 bot (right parallelogram)
# S0 top -> S2 top, S0 bot -> S2 bot (left-to-center parallelogram)
# S1 top -> S2 top, S1 bot -> S2 bot (right-to-center parallelogram)
connections = [
    {"from_type": "anchor", "from_index": 0, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "top", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "anchor", "from_index": 1, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "bot", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "anchor", "from_index": 2, "from_port": "center", "to_type": "stage", "to_index": 1, "to_port": "top", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "anchor", "from_index": 3, "from_port": "center", "to_type": "stage", "to_index": 1, "to_port": "bot", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "stage", "from_index": 0, "from_port": "top", "to_type": "stage", "to_index": 2, "to_port": "top", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "stage", "from_index": 0, "from_port": "bot", "to_type": "stage", "to_index": 2, "to_port": "bot", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "stage", "from_index": 1, "from_port": "top", "to_type": "stage", "to_index": 2, "to_port": "top", "is_tapered": True, "taper_ratio": 0.75},
    {"from_type": "stage", "from_index": 1, "from_port": "bot", "to_type": "stage", "to_index": 2, "to_port": "bot", "is_tapered": True, "taper_ratio": 0.75}
]

spec = {
    "id": "NOVEL_SYMMETRIC_DUAL_SHUTTLE_COMPOUND",
    "architecture_class": "symmetric_dual_shuttle_compound",
    "output_stage": 2,
    "taper_ratio": 0.75,
    "anchors": anchors,
    "stages": stages,
    "connections": connections
}

eng = TopologyInnovationEngineV2(env_x=env_x, env_y=env_y)
for th in [0.00075, 0.00085, 0.00095]:
    res = eng.evaluate_task_specific(spec, th, 2.5, 1.70, 18.0)
    dy = res.get("stroke_dy_mm")
    dx = res.get("parasitic_dx_mm")
    sig = res.get("max_stress_MPa")
    feas = res.get("is_feasible")
    print(f"th={th*1e3:.2f}mm -> dy={dy}, dx={dx}, sig={sig}, feas={feas}, reason={res.get('rejection_reason')}")

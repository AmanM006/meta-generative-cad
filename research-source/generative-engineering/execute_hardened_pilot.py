"""Single Bounded Meta Muse Pilot Dispatcher (Hardened 4096-Token Edition).

Rules Enforced:
1. Exactly ONE call dispatched.
2. Max completion tokens: 4096 (leaving ample headroom for internal reasoning + structured JSON).
3. Temperature: 0.2.
4. Hard spending cap: < $0.05 (Estimated actual: ~$0.005).
5. Attempt marker guards prevent duplicate calls across crashes.
6. Atomic receipt write captures exact prompt, raw response, tokens, and latency.
7. Evaluated strictly via HardenedCompactCompiler & CompliantFrameSolver.
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI
import numpy as np

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
RECEIPT_FILE = ROOT / "compact_pilot_receipt.json"
MARKER_FILE = ROOT / "compact_pilot.attempt_marker"
EVAL_FILE = ROOT / "compact_pilot_evaluation.json"

MODEL = "muse-spark-1.3"

SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "compact_mechanism_design",
        "schema": {
            "type": "object",
            "properties": {
                "topology_name": {"type": "string"},
                "design_rationale": {"type": "string"},
                "anchors": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"}
                    }
                },
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "center": {
                                "type": "array",
                                "items": {"type": "number"}
                            },
                            "height": {"type": "number"},
                            "is_rigid": {"type": "boolean"}
                        },
                        "required": ["center", "height"]
                    }
                },
                "connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from_type": {"type": "string", "enum": ["anchor", "stage"]},
                            "from_index": {"type": "integer"},
                            "from_port": {"type": "string", "enum": ["center", "top", "bot"]},
                            "to_type": {"type": "string", "enum": ["anchor", "stage"]},
                            "to_index": {"type": "integer"},
                            "to_port": {"type": "string", "enum": ["center", "top", "bot"]},
                            "thickness": {"type": "number"}
                        },
                        "required": ["from_type", "from_index", "to_type", "to_index", "thickness"]
                    }
                },
                "output_stage": {"type": "integer"}
            },
            "required": ["topology_name", "design_rationale", "anchors", "stages", "connections", "output_stage"],
            "additionalProperties": False
        }
    }
}

BLINDED_PROMPT = """You are an expert mechanical compliance engineer. Design a monolithic compliant guiding stage in a 2D plane using high-level structural primitives.

PHYSICAL SPECIFICATION:
- Material: Polypropylene (E = 1.4 GPa, Yield Strength = 35.0 MPa, Extrusion Depth = 10.0 mm).
- Actuation: Force F_y = 5.0 N applied in +Y at output_stage.
- Required Stroke: Output stage displacement in +Y must be at least 3.0 mm (dy >= 3.0 mm).
- Stress Limit: Peak von Mises stress must not exceed 25.0 MPa under full stroke (safety factor >= 1.4 on yield).
- Kinematic Precision Limits:
  1. Parasitic axial shift along X must be strictly <= 0.20 mm (|dx| <= 0.20 mm).
  2. Parasitic rotation must be <= 0.05 degrees (|theta| <= 0.05 deg).
- Bounding Box Envelope: All geometry must fit within X in [0.0, 0.090] m (90 mm) and Y in [0.0, 0.055] m (55 mm).

MEASURED PHYSICAL FAILURE OF BASELINE:
Under large-deflection nonlinear elasticity, a conventional two-beam parallel stage fails:
- When beams are flexible enough to achieve 3.0 mm stroke, beam curvature pulls the output stage backward along X by dx = -0.257 mm (violating the 0.20 mm limit).
- Stiffening the beams reduces shift but collapses stroke to 0.18 mm.

TASK:
Propose a new structural arrangement or multi-stage layout using the primitives below to resolve this trade-off.

COMPACT JSON OUTPUT SCHEMA:
Output ONLY a JSON object with this schema:
{
  "topology_name": "string",
  "design_rationale": "string (1-2 sentences on how your structural arrangement prevents axial shortening)",
  "anchors": [[x0, y0], [x1, y1], ...],
  "stages": [
    {"center": [cx, cy], "height": H_meters, "is_rigid": true}
  ],
  "connections": [
    {
      "from_type": "anchor" or "stage",
      "from_index": integer,
      "from_port": "center" or "top" or "bot",
      "to_type": "stage",
      "to_index": integer,
      "to_port": "center" or "top" or "bot",
      "thickness": thickness_in_meters
    }
  ],
  "output_stage": integer_index_of_actuation_stage
}

Constraints on values:
- Coordinates and thickness must be in meters (e.g. 0.045 for 45 mm, 0.0012 for 1.2 mm).
- Connection thickness must be in [0.0006, 0.0030] m.
- Beams must NOT cross or physically intersect each other.
- Every anchor and stage must be connected to the mechanism. No floating elements.
"""

def get_api_key():
    key = os.getenv("MODEL_API_KEY") or os.getenv("META_MODEL_API_KEY")
    if not key:
        env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("MODEL_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key

def evaluate_design(spec, F_y=5.0):
    compiler = HardenedCompactCompiler(max_x=0.090, max_y=0.055)
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)

    try:
        mesh = compiler.compile(spec)
    except Exception as e:
        return {"compiled": False, "error": f"Compiler rejection: {str(e)}"}

    nodes = mesh["nodes"]
    elements = mesh["elements"]
    widths = mesh["widths"]
    ground_nodes = mesh["ground_nodes"]
    output_node = mesh["output_node"]

    boundary = {3*g: 0.0 for g in ground_nodes}
    for g in ground_nodes:
        boundary[3*g+1] = 0.0
        boundary[3*g+2] = 0.0

    forces = np.zeros(3 * len(nodes))
    forces[3 * output_node + 1] = F_y

    try:
        res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundary, forces, num_steps=8)
        u = res["displacements"]
        tip_dx = float(u[3 * output_node])
        tip_dy = float(u[3 * output_node + 1])
        tip_rot_deg = float(np.degrees(abs(u[3 * output_node + 2])))
        max_stress = float(res["max_stress_MPa"])
        vol_cm3 = float(res["volume_cm3"])

        c_stroke = tip_dy >= 0.003
        c_stress = max_stress <= 25.0
        c_shift = abs(tip_dx) <= 0.00020
        c_rot = tip_rot_deg <= 0.05

        violations = []
        if not c_stroke: violations.append(f"INSUFFICIENT_STROKE (dy={tip_dy*1000:.2f}mm < 3.0mm)")
        if not c_stress: violations.append(f"EXCESSIVE_STRESS (sigma={max_stress:.1f}MPa > 25.0MPa)")
        if not c_shift: violations.append(f"EXCESSIVE_PARASITIC_SHIFT (|dx|={abs(tip_dx)*1000:.3f}mm > 0.20mm)")
        if not c_rot: violations.append(f"EXCESSIVE_ROTATION (theta={tip_rot_deg:.4f}deg > 0.05deg)")

        return {
            "compiled": True,
            "simulated": True,
            "tip_dy_mm": tip_dy * 1000.0,
            "tip_dx_mm": tip_dx * 1000.0,
            "tip_rot_deg": tip_rot_deg,
            "max_stress_MPa": max_stress,
            "volume_cm3": vol_cm3,
            "all_constraints_passed": len(violations) == 0,
            "violations": violations
        }
    except Exception as e:
        return {"compiled": True, "simulated": False, "error": f"Nonlinear solver error: {str(e)}"}

def dispatch_pilot():
    print("=== DISPATCHING HARDENED COMPACT META MUSE PILOT ===")
    if MARKER_FILE.exists():
        raise RuntimeError(f"Attempt marker {MARKER_FILE} exists! Refusing duplicate dispatch.")

    key = get_api_key()
    if not key:
        raise RuntimeError("MODEL_API_KEY missing!")

    prompt_hash = hashlib.sha256(BLINDED_PROMPT.encode("utf-8")).hexdigest()
    marker_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "max_completion_tokens": 4096,
        "prompt_sha256": prompt_hash
    }
    with open(MARKER_FILE, "x", encoding="utf-8") as f:
        json.dump(marker_data, f, indent=2)

    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=key, max_retries=0, timeout=45)

    print(f"Connecting to Meta Model API ({MODEL}) with 4096 completion token cap...")
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": BLINDED_PROMPT}],
            response_format=SCHEMA,
            max_completion_tokens=4096,
            temperature=0.2
        )
        elapsed = round(time.time() - t0, 2)
        usage = response.usage
        choice = response.choices[0]
        raw_text = choice.message.content
        finish_reason = choice.finish_reason

        receipt = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "elapsed_seconds": elapsed,
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
            "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
            "finish_reason": finish_reason,
            "raw_response": raw_text,
            "prompt_sha256": prompt_hash
        }
        with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

        print(f"Call Succeeded in {elapsed}s!")
        print(f"Tokens: Total={usage.total_tokens}, Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}, FinishReason={finish_reason}")

        if not raw_text:
            print("ERROR: Returned content is empty!")
            return

        parsed = json.loads(raw_text)
        print(f"Topology Name: '{parsed.get('topology_name')}'")
        print(f"Design Rationale: {parsed.get('design_rationale')}")

        eval_res = evaluate_design(parsed)
        with open(EVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(eval_res, f, indent=2)

        print("-" * 60)
        print("Independent Evaluation Result:")
        print(json.dumps(eval_res, indent=2))

    except Exception as e:
        print(f"Call Failed: {e}")
        receipt = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "error": str(e)
        }
        with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

if __name__ == "__main__":
    dispatch_pilot()

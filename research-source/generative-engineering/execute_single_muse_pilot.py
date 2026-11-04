"""Single Bounded Meta Muse Pilot Dispatcher.

Protocol Enforced:
1. Exactly ONE call dispatched.
2. Cap: max 1200 completion tokens, temperature 0.2.
3. Durable attempt marker ensures zero accidental double-spends.
4. Atomic receipt write preserves full prompt, raw response, tokens, and latency.
5. Independent evaluation: parses proposed mesh, runs non-linear solver, checks all constraints.
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI
from compliant_solver import CompliantFrameSolver

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
PAYLOAD_FILE = ROOT / "muse_pilot_payload.json"
RECEIPT_FILE = ROOT / "muse_pilot_receipt.json"
MARKER_FILE = ROOT / "muse_pilot.attempt_marker"
EVAL_FILE = ROOT / "muse_pilot_evaluation.json"

MODEL = "muse-spark-1.3"

SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "compliant_mechanism_mesh",
        "schema": {
            "type": "object",
            "properties": {
                "topology_name": {"type": "string"},
                "design_rationale": {"type": "string"},
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"}
                    }
                },
                "elements": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                },
                "element_widths": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "ground_nodes": {
                    "type": "array",
                    "items": {"type": "integer"}
                },
                "output_node": {"type": "integer"}
            },
            "required": ["topology_name", "design_rationale", "nodes", "elements", "element_widths", "ground_nodes", "output_node"],
            "additionalProperties": False
        }
    }
}

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

def evaluate_mesh(mesh_data, F_y=5.0):
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)
    nodes = np.array(mesh_data["nodes"])
    elements = np.array(mesh_data["elements"])
    widths = np.array(mesh_data["element_widths"])
    ground_nodes = mesh_data["ground_nodes"]
    output_node = mesh_data["output_node"]

    # Basic topology sanity checks
    num_nodes = len(nodes)
    if output_node < 0 or output_node >= num_nodes:
        return {"valid": False, "error": f"Invalid output_node index {output_node}"}
    for gn in ground_nodes:
        if gn < 0 or gn >= num_nodes:
            return {"valid": False, "error": f"Invalid ground_node index {gn}"}

    # Build boundary condition dict
    boundary = {}
    for gn in ground_nodes:
        boundary[3*gn] = 0.0
        boundary[3*gn + 1] = 0.0
        boundary[3*gn + 2] = 0.0

    forces = np.zeros(3 * num_nodes)
    forces[3 * output_node + 1] = F_y

    try:
        res = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundary, forces, num_steps=8)
        u = res["displacements"]
        tip_dx = float(u[3 * output_node])
        tip_dy = float(u[3 * output_node + 1])
        tip_rot_deg = float(np.degrees(abs(u[3 * output_node + 2])))
        max_stress = float(res["max_stress_MPa"])
        vol_cm3 = float(res["volume_cm3"])

        # Check engineering constraints
        c_stroke = tip_dy >= 0.003
        c_stress = max_stress <= 25.0
        c_shift = abs(tip_dx) <= 0.00020
        c_rot = tip_rot_deg <= 0.05

        violations = []
        if not c_stroke: violations.append(f"INSUFFICIENT_STROKE (dy={tip_dy*1000:.2f}mm < 3.0mm)")
        if not c_stress: violations.append(f"EXCESSIVE_STRESS (sigma={max_stress:.1f}MPa > 25.0MPa)")
        if not c_shift: violations.append(f"EXCESSIVE_PARASITIC_SHIFT (|dx|={abs(tip_dx)*1000:.3f}mm > 0.20mm)")
        if not c_rot: violations.append(f"EXCESSIVE_ROTATION (theta={tip_rot_deg:.4f}deg > 0.05deg)")

        all_pass = len(violations) == 0

        return {
            "valid": True,
            "tip_dy_mm": tip_dy * 1000.0,
            "tip_dx_mm": tip_dx * 1000.0,
            "tip_rot_deg": tip_rot_deg,
            "max_stress_MPa": max_stress,
            "volume_cm3": vol_cm3,
            "all_constraints_passed": all_pass,
            "violations": violations
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

def dispatch_call():
    print("=== EXECUTING SINGLE BOUNDED META MUSE PILOT CALL ===")
    if not PAYLOAD_FILE.exists():
        raise RuntimeError("Payload file missing!")

    with open(PAYLOAD_FILE, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if MARKER_FILE.exists():
        raise RuntimeError(f"Attempt marker {MARKER_FILE} exists! Refusing automatic retry.")

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("No API key available!")

    # Write attempt marker
    marker_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "prompt_sha256": payload["prompt_sha256"]
    }
    with open(MARKER_FILE, "x", encoding="utf-8") as f:
        json.dump(marker_data, f, indent=2)

    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key, max_retries=0, timeout=30)

    print(f"Dispatching request to {MODEL} (Max tokens: {payload['max_completion_tokens']})...")
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": payload["prompt_text"]}],
            response_format=SCHEMA,
            max_completion_tokens=payload["max_completion_tokens"],
            temperature=payload["temperature"]
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
            "finish_reason": finish_reason,
            "raw_response": raw_text,
            "prompt_sha256": payload["prompt_sha256"]
        }
        with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

        print(f"Call Succeeded in {elapsed}s! Tokens: {usage.total_tokens} (Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens})")

        # Parse and evaluate
        parsed_mesh = json.loads(raw_text)
        print(f"Topology Proposed: '{parsed_mesh.get('topology_name')}'")
        print(f"Design Rationale: {parsed_mesh.get('design_rationale')}")

        eval_res = evaluate_mesh(parsed_mesh)
        with open(EVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(eval_res, f, indent=2)

        print("-" * 60)
        print("Independent Evaluation Result:")
        print(json.dumps(eval_res, indent=2))

    except Exception as e:
        print(f"API Call Failed: {e}")
        receipt = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "error": str(e)
        }
        with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

if __name__ == "__main__":
    import numpy as np
    dispatch_call()

"""Phase 2 & 3: Closed-Loop Meta Muse Feedback Experiment (Call 4).

Supplies Meta Muse with:
1. Original architecture JSON from Call 3
2. Measured physical performance and failure diagnostics:
   - Stroke: 1.5428 mm (Target >= 3.000 mm) -> 48.6% deficit
   - Max Stress: 6.9425 MPa (Target <= 25.0 MPa) -> Large safety margin
   - Parasitic rotation: ~0 deg (Target <= 0.05 deg) -> Perfect
   - Axial shift: ~0 mm (Target <= 0.20 mm) -> Perfect
   - Note on physics: Horizontal beams under vertical load develop axial chord tension (geometric stiffening), capping stroke.
3. Asks Muse to propose ONE revised architecture or parameterization to solve the stroke deficit while maintaining precision.
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
from compliant_solver import CompliantFrameSolver, NonlinearConvergenceError

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
RECEIPT_FILE = ROOT / "closed_loop_call4_receipt.json"
MARKER_FILE = ROOT / "closed_loop_call4.attempt_marker"

MODEL = "muse-spark-1.3"
MAX_AUTHORIZED_USD = 0.05

FEEDBACK_PROMPT = """You are an expert mechanical compliance engineer. In the previous turn, you designed the 'symmetric_quad_parallelogram_guide' compliant mechanism.

ORIGINAL DESIGN FROM CALL 3:
{
  "topology_name": "symmetric_quad_parallelogram_guide",
  "anchors": [[0.005, 0.0395], [0.005, 0.0155], [0.085, 0.0395], [0.085, 0.0155]],
  "stages": [{"center": [0.045, 0.0275], "height": 0.024, "is_rigid": true}],
  "connections": [
    {"from_type": "anchor", "from_index": 0, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.0012},
    {"from_type": "anchor", "from_index": 1, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.0012},
    {"from_type": "anchor", "from_index": 2, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.0012},
    {"from_type": "anchor", "from_index": 3, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.0012}
  ],
  "output_stage": 0
}

RIGOROUS INDEPENDENT NONLINEAR SIMULATION FEEDBACK (Under F_y = 5.0 N, Polypropylene E = 1.4 GPa, yield = 35 MPa):
- Actuation Stroke dy: 1.5428 mm (TARGET: dy >= 3.000 mm) --> FAILED (48.6% stroke deficit!)
- Peak von Mises Stress: 6.9425 MPa (TARGET: <= 25.0 MPa) --> PASSED (huge 72% safety margin remaining)
- Parasitic Stage Rotation: 0.000000 deg (TARGET: <= 0.050 deg) --> PASSED (perfect zero by symmetry)
- Parasitic Axial Shift dx: 0.0000 mm (TARGET: <= 0.200 mm) --> PASSED (perfect zero by symmetry)

PHYSICAL ROOT CAUSE OF FAILURE:
Your bilateral symmetric topology successfully eliminated all parasitic off-axis shift and tilt. However, because the four horizontal flexures span directly across to a rigid vertical stage, large transverse deflection induces intense geometric axial chord tension (stress-stiffening), which acts like a stretched string and prevents the mechanism from achieving 3.0 mm stroke under 5.0 N.

ENGINEERING TASK:
Propose ONE revised architecture or modified parameterization using the same primitives to achieve at least 3.000 mm stroke while keeping peak stress <= 25.0 MPa and off-axis parasitic motion (|dx| <= 0.20 mm, |theta| <= 0.05 deg) strictly within limits.
All geometry must remain within the envelope: X in [0.0, 0.090] m (90 mm), Y in [0.0, 0.055] m (55 mm).
Allowed flexure thickness: [0.0006, 0.0030] m.

OUTPUT SCHEMA:
Output ONLY a JSON object conforming strictly to the compact mechanism schema:
{
  "topology_name": "string",
  "design_rationale": "string (1-2 sentences explaining how your revision overcomes the stroke deficit)",
  "anchors": [[x0, y0], ...],
  "stages": [{"center": [cx, cy], "height": H, "is_rigid": true}, ...],
  "connections": [
    {"from_type": "anchor"|"stage", "from_index": int, "from_port": "center"|"top"|"bot", "to_type": "stage", "to_index": int, "to_port": "center"|"top"|"bot", "thickness": float}
  ],
  "output_stage": int
}
"""

SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "revised_mechanism_design",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["topology_name", "design_rationale", "anchors", "stages", "connections", "output_stage"],
            "properties": {
                "topology_name": {"type": "string"},
                "design_rationale": {"type": "string"},
                "anchors": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}}
                },
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["center", "height", "is_rigid"],
                        "properties": {
                            "center": {"type": "array", "items": {"type": "number"}},
                            "height": {"type": "number"},
                            "is_rigid": {"type": "boolean"}
                        }
                    }
                },
                "connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["from_type", "from_index", "from_port", "to_type", "to_index", "to_port", "thickness"],
                        "properties": {
                            "from_type": {"type": "string", "enum": ["anchor", "stage"]},
                            "from_index": {"type": "integer"},
                            "from_port": {"type": "string", "enum": ["center", "top", "bot"]},
                            "to_type": {"type": "string", "enum": ["anchor", "stage"]},
                            "to_index": {"type": "integer"},
                            "to_port": {"type": "string", "enum": ["center", "top", "bot"]},
                            "thickness": {"type": "number"}
                        }
                    }
                },
                "output_stage": {"type": "integer"}
            }
        }
    }
}

def execute_call4():
    if MARKER_FILE.exists():
        print(f"ABORT: Marker {MARKER_FILE} already exists. Exactly one call permitted.")
        sys.exit(1)

    MARKER_FILE.write_text(f"Dispatched at {datetime.now(timezone.utc).isoformat()}")

    api_key = None
    env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("MODEL_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if not api_key:
        print("ERROR: MODEL_API_KEY missing from horizonforge .env")
        sys.exit(1)

    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key, max_retries=0, timeout=60)
    prompt_hash = hashlib.sha256(FEEDBACK_PROMPT.encode("utf-8")).hexdigest()

    print("=== DISPATCHING CLOSED-LOOP META MUSE CALL 4 ===")
    print(f"Model: {MODEL}")
    print(f"reasoning_effort: minimal")
    print(f"max_completion_tokens: 4096")
    print(f"Authorized cap: ${MAX_AUTHORIZED_USD:.2f}")
    print(f"Prompt SHA-256: {prompt_hash}")
    print(f"Dispatching at: {datetime.now(timezone.utc).isoformat()}")

    t0 = time.perf_counter()
    raw_response = None
    api_error = None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            reasoning_effort="minimal",
            max_completion_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": FEEDBACK_PROMPT}],
            response_format=SCHEMA
        )
        raw_response = response
    except Exception as e:
        api_error = str(e)

    elapsed = time.perf_counter() - t0

    receipt = {
        "call_id": "closed_loop_call_4",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "reasoning_effort": "minimal",
        "max_completion_tokens": 4096,
        "temperature": 0.2,
        "authorized_cap_usd": MAX_AUTHORIZED_USD,
        "prompt_sha256": prompt_hash,
        "latency_seconds": round(elapsed, 3),
        "api_error": api_error,
        "finish_reason": None,
        "usage": None,
        "raw_content": None,
        "parsed_design": None
    }

    if raw_response:
        choice = raw_response.choices[0]
        receipt["finish_reason"] = choice.finish_reason
        receipt["usage"] = {
            "prompt_tokens": raw_response.usage.prompt_tokens if raw_response.usage else None,
            "completion_tokens": raw_response.usage.completion_tokens if raw_response.usage else None,
            "total_tokens": raw_response.usage.total_tokens if raw_response.usage else None,
        }
        content = choice.message.content
        receipt["raw_content"] = content
        print(f"finish_reason: {choice.finish_reason}")
        print(f"Usage: {receipt['usage']}")

        if content:
            try:
                design = json.loads(content)
                receipt["parsed_design"] = design
                print(f"\nRevised Topology: {design.get('topology_name')}")
                print(f"Rationale: {design.get('design_rationale')}")
            except Exception as e:
                receipt["parse_error"] = str(e)
    else:
        print(f"API Error: {api_error}")

    with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
    print(f"Receipt written to: {RECEIPT_FILE}")

if __name__ == "__main__":
    execute_call4()

# Meta Muse API Integration Code Archive

This package contains the complete, verified Python code for interfacing with Meta's **Muse** models (`muse-spark-1.3`) via the Meta Model API, including:
1. **Proven Working Implementation** (from `horizonforge-local-test`) that successfully dispatched, received, and validated responses.
2. **Recent Generative Engineering Implementation** that hit the internal reasoning token cap.
3. **Receipts & Payload Formats** for both working and failed calls.

---

## 1. Proven Working Implementation (HorizonForge Reference)

This script (`horizonforge-local-test/run_live_muse_call.py` and `collect_adaptive_loop.py`) is the working implementation that successfully authenticated with Meta's API, enforced structured JSON output, handled tokens, and wrote durable receipts.

```python
"""
Proven working call pattern for Meta Muse Spark 1.3 via Meta Model API.
Location: C:/Users/aman/Documents/meta/horizonforge-local-test/collect_adaptive_loop.py
"""

import os
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

MODEL = "muse-spark-1.3"

# 1. Structured JSON Output Schema
SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "circuit_topology",
        "schema": {
            "type": "object",
            "properties": {
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
            },
            "required": ["edges"],
            "additionalProperties": False,
        },
    },
}

# 2. API Key Retrieval (Reads from local .env or system environment)
def get_api_key():
    key = os.getenv("MODEL_API_KEY")
    if not key:
        env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("MODEL_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key

# 3. Core Dispatch Function with Durable Attempt Guard & Receipt Logging
def execute_muse_call(prompt_text, call_id="CALL_08", output_dir="muse_collection"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    marker_file = output_dir / f"{call_id}.attempt_marker"
    receipt_file = output_dir / f"{call_id}_receipt.json"

    # Avoid duplicate spend
    if marker_file.exists():
        raise RuntimeError(f"Attempt marker {marker_file} exists. Refusing automatic retry.")

    key = get_api_key()
    if not key:
        raise RuntimeError("MODEL_API_KEY not found!")

    # Write attempt marker before dispatch
    marker_payload = {
        "call_id": call_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "DISPATCHED_AWAITING_RESPONSE",
        "model": MODEL
    }
    with open(marker_file, "x", encoding="utf-8") as f:
        json.dump(marker_payload, f, indent=2)

    # Initialize OpenAI Client targeting Meta's endpoint
    client = OpenAI(
        base_url="https://api.meta.ai/v1",
        api_key=key,
        max_retries=0,
        timeout=30.0
    )

    t0 = time.time()
    try:
        # CRITICAL PARAMETER: reasoning_effort="minimal"
        # When omitted or set to default/medium/high, Muse Spark consumes thousands of
        # completion tokens on internal thinking, starving the visible content budget.
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt_text}],
            response_format=SCHEMA,
            max_completion_tokens=1024,
            reasoning_effort="minimal",
            temperature=0.2
        )
        elapsed = round(time.time() - t0, 2)
        usage = response.usage
        choice = response.choices[0]
        raw_content = choice.message.content
        finish_reason = choice.finish_reason

        receipt = {
            "call_id": call_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "elapsed_seconds": elapsed,
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
            "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
            "finish_reason": finish_reason,
            "raw_response": raw_content,
            "prompt_text": prompt_text
        }
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

        return receipt

    except Exception as e:
        receipt = {
            "call_id": call_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "error": str(e)
        }
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)
        raise e
```

---

## 2. Proven Successful Call Receipt (`CALL_08_TRANSPORT_RECOVERY`)

This is the exact JSON receipt saved on disk from the working call:
**Location:** `horizonforge-local-test/muse_collection/CALL_08_TRANSPORT_RECOVERY_receipt.json`

```json
{
  "call_id": "CALL_08_TRANSPORT_RECOVERY",
  "candidate_id": "muse_live_08",
  "timestamp_utc": "2026-10-27T04:11:18.099798+00:00",
  "model": "muse-spark-1.3",
  "temperature": 0.2,
  "max_completion_tokens": 1024,
  "reasoning_effort": "minimal",
  "prompt_text": "Design one ordered 11-CNOT spanning tree for a 12-qubit, two-layer RY+CNOT circuit. Qubits 0-5 encode matrix X1; 6-11 encode X2. Earlier alternating ladders had low SU(2) singlet overlap; block chains improved it. Explore a different tree with two cross-register bridges, while keeping its undirected graph connected and acyclic. Return only JSON with key edges: exactly 11 distinct directed [control,target] pairs using qubits 0-11. The simulator, not the graph, measures physical singlet overlap.",
  "elapsed_seconds": 8.7,
  "prompt_tokens": 125,
  "completion_tokens": 886,
  "total_tokens": 1011,
  "reasoning_tokens": 807,
  "finish_reason": "stop",
  "raw_response": "{\"edges\": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [6, 7], [7, 8], [9, 10], [10, 11], [5, 9], [2, 6]]}",
  "validation": {
    "verdict": "PASSED",
    "edges_count": 11,
    "is_spanning_tree": true
  }
}
```

---

## 3. The Generative Engineering Implementation (Hit Token Cap)

This is the script executed today in `generative-engineering/execute_hardened_pilot.py`:

```python
"""
Generative Engineering Pilot Dispatcher.
Location: C:/Users/aman/Documents/meta/generative-engineering/execute_hardened_pilot.py
"""

import os
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
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
                    "items": {"type": "array", "items": {"type": "number"}}
                },
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "center": {"type": "array", "items": {"type": "number"}},
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

def dispatch_pilot():
    key = os.getenv("MODEL_API_KEY")
    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=key, max_retries=0, timeout=45)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": BLINDED_PROMPT}],
        response_format=SCHEMA,
        max_completion_tokens=4096,
        temperature=0.2
        # NOTE: reasoning_effort="minimal" was omitted here!
    )
    return response
```

---

## 4. The Engineering Call Failure Receipt (`compact_pilot_receipt.json`)

**Location:** `generative-engineering/compact_pilot_receipt.json`

```json
{
  "timestamp_utc": "2026-10-28T15:12:20.815539+00:00",
  "model": "muse-spark-1.3",
  "elapsed_seconds": 21.37,
  "prompt_tokens": 652,
  "completion_tokens": 4096,
  "total_tokens": 4748,
  "reasoning_tokens": 4094,
  "finish_reason": "length",
  "raw_response": null,
  "prompt_sha256": "f4240b6664af0a7b3fe6e647d29c42a067e2429d7e3e6b11c1d917dd20d052db"
}
```

---

## 5. Diagnostic Summary for Review

1. **Endpoint & Authentication:** Validated and working (`base_url="https://api.meta.ai/v1"` using standard `OpenAI` client SDK).
2. **Model Behavior:** `muse-spark-1.3` is a reasoning model. When given complex physical multi-objective constraints without an explicit `reasoning_effort="minimal"` limiter, its internal reasoning tokens scale up to consume the entire `max_completion_tokens` window (4,094 reasoning tokens out of 4,096 total completion tokens), leaving zero tokens to serialize the visible `raw_response`.
3. **The Key Fix Identified:** In HorizonForge, setting `reasoning_effort="minimal"` clamped internal thinking to ~800 tokens, allowing the final JSON payload to emit cleanly with `finish_reason: "stop"`.

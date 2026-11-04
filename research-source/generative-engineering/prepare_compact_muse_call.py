"""Protocol & Payload Builder for Compact Meta Muse Engineering Challenge.

Prompt characteristics:
1. Short, concise instructions (~300 words).
2. Explicitly states physical requirements: F_y=5.0N, dy>=3.0mm, sigma<=25.0MPa, |dx|<=0.20mm, |theta|<=0.05deg.
3. Mentions failure: conventional 2-beam parallel stage curves, causing parasitic arc shortening |dx| > 0.20mm when flexible, or collapsing stroke when thickened.
4. Requires high-level structural primitives: anchors, stages, connections, output_stage.
5. NO hints about specific topology names (no mention of 'folded', 'compound', 'roberts', 'cross-axis').
6. Max completion tokens: 1024, temperature: 0.2.
"""

import json
import hashlib
from pathlib import Path

COMPACT_PROMPT = """You are an expert mechanical compliance engineer. Design a monolithic compliant guiding stage in a 2D plane using high-level structural primitives.

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
- Every anchor and stage must be connected to the mechanism. No floating elements.
"""

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

def save_recovery_payload():
    prompt_bytes = COMPACT_PROMPT.encode("utf-8")
    prompt_hash = hashlib.sha256(prompt_bytes).hexdigest()
    
    payload = {
        "model": "muse-spark-1.3",
        "max_completion_tokens": 1024,
        "temperature": 0.2,
        "prompt_sha256": prompt_hash,
        "prompt_text": COMPACT_PROMPT,
        "estimated_prompt_tokens": len(COMPACT_PROMPT.split()) * 1.3,
        "estimated_cost_usd": 0.003
    }
    
    out_file = Path("C:/Users/aman/Documents/meta/generative-engineering/compact_muse_payload.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    schema_file = Path("C:/Users/aman/Documents/meta/generative-engineering/compact_schema.json")
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, indent=2)

    print(f"Compact Muse Payload Saved: {out_file}")
    print(f"  Prompt SHA256: {prompt_hash}")
    print(f"  Estimated Cost: ~${payload['estimated_cost_usd']:.4f}")

if __name__ == "__main__":
    save_recovery_payload()

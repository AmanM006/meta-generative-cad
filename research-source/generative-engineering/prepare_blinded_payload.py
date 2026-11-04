"""Protocol & Blinded Payload Builder for Meta Muse Engineering Challenge.

REVISED BLINDED SPECIFICATION:
1. Retires all claims that classical two-beam designs are mathematically impossible.
2. Focuses objectively on Pareto performance: minimizing volume (mass) and parasitic motion (dx, theta)
   while meeting stroke (dy >= 3.0 mm) and stress limits (sigma <= 25.0 MPa).
3. Uses the compact architecture compiler and hardened geometry validator.
4. Contains zero topology hints (no mention of 'folded', 'compound', 'roberts', 'cross-axis').
5. Explicitly configures reasoning_effort="minimal" and max_completion_tokens=2048 to avoid
   reasoning token cap exhaustion.
"""

import json
import hashlib
from pathlib import Path

REVISED_BLINDED_PROMPT = """You are an expert mechanical compliance engineer. Design a monolithic compliant guiding stage in a 2D plane using high-level structural primitives.

OBJECTIVE & DESIGN CHALLENGE:
Your objective is to minimize total mechanism volume (material mass) and eliminate parasitic off-axis motion (parasitic axial shift |dx| and parasitic rotation |theta|) while satisfying all structural compliance requirements.

PHYSICAL SPECIFICATION & STRICT LIMITS:
- Material: Polypropylene (Young's Modulus E = 1.4 GPa, Yield Strength = 35.0 MPa, Extrusion Depth = 10.0 mm).
- Actuation: Point force F_y = 5.0 N applied in the +Y direction at the output stage.
- Required Stroke: Output stage displacement in +Y must be at least 3.0 mm (dy >= 3.000 mm).
- Maximum Allowable Stress: Peak von Mises stress throughout the mechanism must not exceed 25.0 MPa under full stroke (safety factor >= 1.4 on 35 MPa yield).
- Kinematic Precision Requirements:
  1. Parasitic axial shift along X must be strictly <= 0.200 mm (|dx| <= 0.200 mm). Zero shift is ideal.
  2. Parasitic stage rotation must be strictly <= 0.050 degrees (|theta| <= 0.050 deg). Zero rotation is ideal.
- Design Envelope Bounding Box: All nodes, beams, and stages must reside strictly within X in [0.0, 0.090] m (90 mm) and Y in [0.0, 0.055] m (55 mm).

HIGH-LEVEL COMPACT PRIMITIVES SCHEMA:
Represent your design using structural anchors, intermediate or output stages, and flexure beam connections.
Output ONLY a JSON object conforming strictly to this structure:
{
  "topology_name": "string (descriptive name)",
  "design_rationale": "string (1-2 sentences explaining structural load paths and motion decoupling)",
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

GEOMETRIC & COMPILER RULES:
- All dimensions must be in meters (e.g., 0.045 for 45 mm, 0.0012 for 1.2 mm).
- Beam thickness must be within [0.0006, 0.0030] m.
- Every anchor and stage must be mechanically connected into a single monolithic kinematic graph.
- Crossing or self-intersecting beams are physically forbidden and will be rejected.
- All elements and stage endpoints must lie strictly inside the 90 x 55 mm boundary.
"""

REVISED_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "blinded_mechanism_design",
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

def build_and_save_payload():
    prompt_bytes = REVISED_BLINDED_PROMPT.encode("utf-8")
    prompt_hash = hashlib.sha256(prompt_bytes).hexdigest()

    payload = {
        "model": "muse-spark-1.3",
        "reasoning_effort": "minimal",
        "max_completion_tokens": 2048,
        "temperature": 0.2,
        "prompt_sha256": prompt_hash,
        "prompt_text": REVISED_BLINDED_PROMPT,
        "estimated_prompt_tokens": int(len(REVISED_BLINDED_PROMPT.split()) * 1.3),
        "estimated_cost_usd": 0.004,
        "authorized_cap_usd": 0.05
    }

    out_payload = Path("C:/Users/aman/Documents/meta/generative-engineering/blinded_muse_payload.json")
    with open(out_payload, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    out_schema = Path("C:/Users/aman/Documents/meta/generative-engineering/blinded_schema.json")
    with open(out_schema, "w", encoding="utf-8") as f:
        json.dump(REVISED_SCHEMA, f, indent=2)

    print(f"Blinded Muse Payload Saved: {out_payload}")
    print(f"  Prompt SHA256: {prompt_hash}")
    print(f"  Configuration: reasoning_effort=minimal, max_tokens=2048")
    print(f"  Estimated Cost: ~${payload['estimated_cost_usd']:.4f} (Cap: ${payload['authorized_cap_usd']:.2f})")

if __name__ == "__main__":
    build_and_save_payload()

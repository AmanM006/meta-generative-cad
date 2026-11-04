"""Blinded Meta Muse Prompt Formulation and Call Runner.

Strict Rules Enforced:
1. NO HINTS about compound folded beams, inverted stages, or specific topologies.
2. Only provides:
   - Functional requirements: Stroke >= 3.0 mm under F_y = 5.0 N.
   - Engineering constraints: Max stress <= 25.0 MPa, Parasitic shift |dx| <= 0.20 mm, rotation <= 0.05 deg.
   - Material properties: Polypropylene (E = 1.4 GPa, yield = 35 MPa, depth = 10 mm).
   - Envelope: Max width 100 mm, Max height 60 mm.
   - Measured failure of classical 4-bar baseline under nonlinear mechanics:
     * When stroke is achieved (3.0 mm), parasitic shortening dx = -0.257 mm violates straightness (limit 0.20 mm).
     * If beam thickness is increased to avoid shift, stroke collapses to 0.185 mm.
   - Generic 2D Frame element syntax: nodes [[x, y], ...], elements [[n1, n2], ...], beam_thicknesses [h, ...], ground_nodes [...], load_node index.
"""

import os
import json
import hashlib
from pathlib import Path

# BLINDED PROMPT SPECIFICATION
BLINDED_MUSE_PROMPT = """You are an expert mechanical compliance engineer. Design a monolithic compliant guiding stage in a 2D plane.

ENGINEERING SPECIFICATION:
- Material: Polypropylene (Young's Modulus E = 1.4 GPa, Yield Strength = 35.0 MPa).
- Out-of-plane extrusion depth: 10.0 mm.
- Actuation: Point load F_y = 5.0 N applied at a designated output node.
- Required Primary Stroke: The output node must displace in +Y by at least 3.0 mm (dy >= 3.0 mm).
- Stress Constraint: Peak von Mises stress must not exceed 25.0 MPa under full deflection (safety factor >= 1.4 on yield).
- Kinematic Precision Constraints:
  1. Parasitic axial shift along X must be strictly less than 0.20 mm (|dx| <= 0.20 mm).
  2. Parasitic rotation of the output node must be less than 0.05 degrees (|theta| <= 0.05 deg).
- Bounding Box Envelope: Total mechanism width <= 90.0 mm (X in [0, 0.090] m), height <= 55.0 mm (Y in [0, 0.055] m).

PHYSICAL FAILURE DIAGNOSTIC OF EXISTING DESIGN:
A conventional two-beam parallel stage with flexure beams connecting ground to an output carriage was tested under large-deflection nonlinear finite element analysis. It failed:
1. When flexures are flexible enough to achieve dy = 3.0 mm, beam curvature inevitably pulls the carriage backward along X by dx = -0.257 mm (exceeding the 0.20 mm limit).
2. If the optimizer thickens the beams to stiffen the X-axis, the stroke collapses to only 0.18 mm under the 5.0 N force.
A simple two-beam parallel mechanism cannot simultaneously satisfy both constraints.

YOUR TASK:
Synthesize an architectural modification or new mechanism topology that resolves this trade-off and satisfies all constraints.
Do NOT output generic advice. Output an exact, connected 2D beam mesh in valid JSON.

JSON SCHEMA REQUIREMENT:
Output ONLY a JSON object with these keys:
{
  "topology_name": "string (short descriptive name)",
  "design_rationale": "string (2-3 sentences explaining the kinematic mechanism used to prevent axial shortening)",
  "nodes": [[x0, y0], [x1, y1], ...],
  "elements": [[node_i, node_j], ...],
  "element_widths": [thickness_in_meters, ...],
  "ground_nodes": [node_index_1, node_index_2, ...],
  "output_node": integer_index_of_actuation_and_guided_stage
}

Notes on the mesh:
- Coordinates x, y and element_widths must be in meters (e.g. 0.040 for 40 mm, 0.001 for 1 mm).
- Every node must be connected. No floating elements.
- The ground_nodes will be clamped (dx=0, dy=0, dtheta=0).
- The actuation load F_y = 5.0 N will be applied at output_node.
"""

def generate_call_payload():
    prompt_bytes = BLINDED_MUSE_PROMPT.encode("utf-8")
    prompt_hash = hashlib.sha256(prompt_bytes).hexdigest()
    
    payload = {
        "model": "muse-spark-1.3",
        "max_completion_tokens": 1200,
        "temperature": 0.2,
        "prompt_sha256": prompt_hash,
        "prompt_text": BLINDED_MUSE_PROMPT,
        "estimated_prompt_tokens": len(BLINDED_MUSE_PROMPT.split()) * 1.3,
        "estimated_cost_usd": 0.003
    }
    
    out_path = Path("C:/Users/aman/Documents/meta/generative-engineering/muse_pilot_payload.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    print("Blinded Meta Muse Pilot Payload Prepared:")
    print(f"  Prompt SHA256: {prompt_hash}")
    print(f"  Estimated Cost: ~${payload['estimated_cost_usd']:.4f}")
    print(f"  Saved to: {out_path}")

if __name__ == "__main__":
    generate_call_payload()

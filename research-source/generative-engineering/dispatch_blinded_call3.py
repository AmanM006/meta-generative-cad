"""Blinded Meta Muse Experiment Dispatcher — Authorization Call 3.

Configuration per user authorization:
- Model: muse-spark-1.3
- reasoning_effort: "minimal"
- max_completion_tokens: 4096
- Temperature: 0.2
- Maximum authorized spend: $0.05
- Exactly ONE call, zero automatic retries.
- Blinded prompt: no topology hints, no impossibility claims.
- Raw response preserved unmodified for independent review.
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
RECEIPT_FILE = ROOT / "blinded_call3_receipt.json"
MARKER_FILE = ROOT / "blinded_call3.attempt_marker"

MODEL = "muse-spark-1.3"
MAX_AUTHORIZED_USD = 0.05

BLINDED_PROMPT = """You are an expert mechanical compliance engineer. Design a monolithic compliant guiding stage in a 2D plane using high-level structural primitives.

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

SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "blinded_mechanism_design",
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

def run_experiment():
    # Guard: exactly one call
    if MARKER_FILE.exists():
        print(f"ABORT: Attempt marker {MARKER_FILE} already exists. Refusing to dispatch a second call.")
        sys.exit(1)

    MARKER_FILE.write_text(f"Dispatched at {datetime.now(timezone.utc).isoformat()}")

    # Load key from the same .env used by previous successful calls
    api_key = None
    env_candidates = [
        Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env"),
        ROOT / ".env",
    ]
    for env_file in env_candidates:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                for prefix in ("MODEL_API_KEY=", "META_API_KEY=", "META_MODEL_API_KEY="):
                    if line.startswith(prefix):
                        api_key = line.split("=", 1)[1].strip()
                        print(f"Loaded API key from: {env_file}")
                        break
                if api_key:
                    break
        if api_key:
            break

    if not api_key:
        # Try environment as last resort
        api_key = (os.environ.get("MODEL_API_KEY") or
                   os.environ.get("META_API_KEY") or
                   os.environ.get("META_MODEL_API_KEY"))

    if not api_key:
        print("ERROR: No valid API key found in known .env files or environment.")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.meta.ai/v1")
    prompt_hash = hashlib.sha256(BLINDED_PROMPT.encode("utf-8")).hexdigest()

    print("=== BLINDED META MUSE EXPERIMENT — CALL 3 ===")
    print(f"Model: {MODEL}")
    print(f"reasoning_effort: minimal")
    print(f"max_completion_tokens: 4096")
    print(f"Authorized cap: ${MAX_AUTHORIZED_USD:.2f}")
    print(f"Prompt SHA-256: {prompt_hash}")
    print(f"Dispatching at: {datetime.now(timezone.utc).isoformat()}")
    print()

    t_start = time.perf_counter()
    raw_response = None
    api_error = None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            reasoning_effort="minimal",
            max_completion_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": BLINDED_PROMPT}],
            response_format=SCHEMA
        )
        raw_response = response
    except Exception as e:
        api_error = str(e)

    t_elapsed = time.perf_counter() - t_start

    receipt = {
        "call_id": "blinded_call_3",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "reasoning_effort": "minimal",
        "max_completion_tokens": 4096,
        "temperature": 0.2,
        "authorized_cap_usd": MAX_AUTHORIZED_USD,
        "prompt_sha256": prompt_hash,
        "latency_seconds": round(t_elapsed, 3),
        "api_error": api_error,
        "finish_reason": None,
        "usage": None,
        "raw_content": None,
        "parsed_design": None
    }

    if raw_response:
        receipt["finish_reason"] = raw_response.choices[0].finish_reason
        receipt["usage"] = {
            "prompt_tokens": raw_response.usage.prompt_tokens if raw_response.usage else None,
            "completion_tokens": raw_response.usage.completion_tokens if raw_response.usage else None,
            "total_tokens": raw_response.usage.total_tokens if raw_response.usage else None,
        }
        content = raw_response.choices[0].message.content
        receipt["raw_content"] = content
        print(f"finish_reason: {receipt['finish_reason']}")
        print(f"Usage: {receipt['usage']}")
        print(f"Raw content length: {len(content) if content else 0} chars")

        if content:
            try:
                design = json.loads(content)
                receipt["parsed_design"] = design
                print(f"\nTopology Name: {design.get('topology_name', 'N/A')}")
                print(f"Design Rationale: {design.get('design_rationale', 'N/A')}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                receipt["parse_error"] = str(e)
    else:
        print(f"API error: {api_error}")

    # Write receipt atomically
    with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
    print(f"\nReceipt written to: {RECEIPT_FILE}")

    # Evaluate if design was parsed
    if receipt.get("parsed_design"):
        evaluate_design(receipt["parsed_design"])
    else:
        print("\nNo parsed design to evaluate. Stopping.")

def evaluate_design(design):
    print("\n=== HARDENED COMPILER VALIDATION ===")
    compiler = HardenedCompactCompiler()
    try:
        mesh = compiler.compile(design)
        nodes = mesh["nodes"]
        elements = mesh["elements"]
        element_widths = mesh["widths"]
        ground_nodes = mesh["ground_nodes"]
        idx_output = mesh["output_node"]
        print(f"Geometry Validation: PASS — Nodes: {len(nodes)}, Elements: {len(elements)}, Ground Nodes: {ground_nodes}")
    except Exception as e:
        print(f"Geometry Validation: FAIL — {e}")
        return

    print("\n=== NONLINEAR PHYSICS SIMULATION (Mesh Convergence) ===")
    solver = CompliantFrameSolver(E=1.4e9, yield_strength=35e6, depth=0.010)

    # Fully constrain all 3 DOFs for EVERY ground anchor returned by compiler
    boundary_dofs = {
        3 * gn + dof: 0.0
        for gn in ground_nodes
        for dof in range(3)
    }

    F_y = 5.0
    forces = np.zeros(3 * len(nodes))
    forces[3 * idx_output + 1] = F_y

    results_table = []
    for n_elem in [6, 12, 24]:
        try:
            m = compiler.compile(design, n_elem_per_beam=n_elem)
            n_nodes = m["nodes"]
            n_elems = m["elements"]
            n_widths = m["widths"]
            b_dofs = {3 * gn + d: 0.0 for gn in m["ground_nodes"] for d in range(3)}
            f_vec = np.zeros(3 * len(n_nodes))
            f_vec[3 * m["output_node"] + 1] = F_y

            res = solver.solve_nonlinear_newton_raphson(
                n_nodes, n_elems, n_widths,
                boundary_dofs=b_dofs,
                external_forces=f_vec,
                num_steps=10,
                tol=1e-6
            )
            u = res["displacements"]
            dy = float(u[3 * m["output_node"] + 1]) * 1000.0
            dx = float(u[3 * m["output_node"]]) * 1000.0
            theta = float(np.degrees(abs(u[3 * m["output_node"] + 2])))
            sigma = res["max_stress_MPa"]

            c_stroke = dy >= 3.000000
            c_stress = sigma <= 25.000000
            c_rot = theta <= 0.050000
            c_shift = abs(dx) <= 0.200000
            all_pass = c_stroke and c_stress and c_rot and c_shift

            results_table.append({
                "n_elem_per_beam": n_elem, "dy": dy, "dx": dx, "theta": theta, "sigma": sigma,
                "pass": all_pass
            })
            print(f"N_elem={n_elem}: dy={dy:.4f}mm, sigma={sigma:.3f}MPa, theta={theta:.6f}deg, dx={dx:.4f}mm | {'STRICT PASS' if all_pass else 'FAIL (Stroke)'}")
        except NonlinearConvergenceError as e:
            print(f"N_elem={n_elem}: Convergence FAILED — {e}")
        except Exception as e:
            print(f"N_elem={n_elem}: Solver ERROR — {e}")

    return results_table

if __name__ == "__main__":
    run_experiment()

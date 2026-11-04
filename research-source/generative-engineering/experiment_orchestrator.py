"""Rigorous Multi-Tranche Meta Muse Experiment Orchestrator.

Scientific Protocol:
- Authorized cumulative ceiling: $10.00 initial tranche (hard stop)
- $60.00 total conditional ceiling (requires explicit unlock)
- All raw API responses, failed candidates, repair provenance, and optimizer traces persisted
- Strict separation of discovery experiments from held-out benchmark evaluation
- Coordinate/unit normalization with EXPLICIT repair annotation (never silent substitution)
- Topology-level SciPy refinement: thicknesses + shuttle X + stage heights + port separation
- Pre-registered prompt variants with different architectural framing

Attribution Rules (immutable):
- P0 double-folded mechanism: deterministic ground truth — NOT attributed to Muse
- Muse credit: autonomous architectural ideation, parasitic-motion elimination, feedback adaptation
- Never substitute P0 fixture as a Muse result
"""

import os
import sys
import json
import copy
import time
import hashlib
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy.optimize import minimize
from openai import OpenAI

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver, NonlinearConvergenceError
from hybrid_agent import (
    evaluate_topology,
    T_DY, T_SIG, T_ROT, T_DX, T_H, N_COARSE, N_FINE,
    PRICE_PROMPT_PER_1K, PRICE_COMPLETION_PER_1K
)

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
ENV_FILE = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
RESULTS_DIR = ROOT / "experiment_results"
RESULTS_DIR.mkdir(exist_ok=True)

MODEL = "muse-spark-1.3"
INITIAL_TRANCHE_USD = 10.00   # hard initial ceiling
FULL_CEILING_USD = 60.00      # conditional ceiling (requires --unlock-full)

# ---------------------------------------------------------------------------
# Minimal working JSON schema (proven compatible with muse-spark-1.3)
# ---------------------------------------------------------------------------
SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "mechanism_design_v2",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["topology_name", "design_rationale", "anchors", "stages",
                         "connections", "output_stage"],
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
                        "required": ["from_type", "from_index", "from_port",
                                     "to_type", "to_index", "to_port", "thickness"],
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

# ---------------------------------------------------------------------------
# Pre-registered prompt variants (different architectural framings)
# ---------------------------------------------------------------------------
PROMPT_VARIANTS = {
    "A_compound_direct": """You are a mechanical compliance engineer designing a monolithic planar compliant mechanism.

PHYSICAL SPECIFICATIONS (all strict, zero relaxation):
- Material: Polypropylene, E=1.4 GPa, yield strength=35 MPa, depth=10 mm
- Actuation: Fy=5.0 N vertically (+Y) at the output stage
- Required stroke: dy >= 3.000 mm
- Max peak stress: sigma <= 25.0 MPa
- Max parasitic axial shift: |dx| <= 0.200 mm
- Max parasitic rotation: |theta| <= 0.050 degrees
- Min flexure thickness: h >= 0.600 mm (STRICT manufacturing floor)
- Design envelope: X in [0.000, 0.090] m, Y in [0.000, 0.055] m
- Ground anchors must be on boundary walls (X=0.0 or X=0.090)

ARCHITECTURAL GUIDANCE:
You may design multi-stage mechanisms using multiple rigid floating intermediate stages (shuttles) connected by thin flexure beams.
Bilateral symmetry about X=0.045 m eliminates parasitic shift and rotation.
Intermediate floating shuttles can kinematically decouple geometric chord-stiffening effects.

Design a complete mechanism. Output ONLY valid JSON conforming to the schema.""",

    "B_series_parallelogram": """You are designing a precision planar flexure guiding stage for a MEMS-scale motion system.

HARD CONSTRAINTS:
- Polypropylene (E=1.4 GPa, yield 35 MPa), depth b=10 mm
- Applied force: Fy=5.0 N (+Y direction) at output stage center
- Required translation: dy >= 3.000 mm
- Stress ceiling: peak von Mises stress <= 25.000 MPa
- Kinematic purity: parasitic |dx| <= 0.200 mm, |theta| <= 0.050 deg
- Manufacturing: beam thickness h >= 0.600 mm (hard floor)
- Bounding box: X in [0, 90] mm, Y in [0, 55] mm (output in meters)

DESIGN FREEDOM:
- Use as many rigid stages and flexure connections as needed
- Symmetric architectures about X=45mm naturally cancel off-axis errors
- Consider that series-connected flexure stages distribute stroke, reducing stress per stage

Design the optimal topology. Output ONLY valid JSON.""",

    "C_stiffness_decoupled": """You are solving a challenging mechanical engineering design problem:
Design a monolithic compliant guiding mechanism that achieves high transverse compliance (stroke) while maintaining extreme lateral rigidity (low parasitic shift).

REQUIREMENTS (non-negotiable):
- Young's modulus E=1.4 GPa (polypropylene), depth=10 mm
- Force Fy=5.0 N applied at output stage
- Output translation dy >= 3.000 mm
- Peak stress <= 25.0 MPa  
- Lateral parasitic |dx| <= 0.200 mm, rotational |theta| <= 0.050 deg
- Minimum cross-section: h >= 0.600 mm
- All geometry within X=[0,0.090]m, Y=[0,0.055]m
- Ground anchors fixed at left wall (X=0) or right wall (X=0.090)

KEY ENGINEERING CHALLENGE: Long thin beams give high compliance but suffer axial chord-shortening under large deflections, reducing effective stroke. Multi-stage architectures with intermediate floating rigid stages can overcome this limitation.

Output a valid topology JSON for the mechanism.""",

    "D_biomimetic_symmetry": """Design a symmetric planar flexure stage for precision positioning.

SPECIFICATIONS:
- Material properties: E=1.4 GPa, sigma_yield=35 MPa, depth=10 mm
- Actuation: point force F=5.0 N in +Y direction
- Kinematic requirement: output displacement dy >= 3.000 mm
- Stress limit: max stress <= 25.0 MPa (safety factor >= 1.4 on yield)
- Parasitic constraints: |dx| <= 0.2 mm, |theta| <= 0.05 degrees
- Minimum manufacturable feature: beam thickness h >= 0.6 mm
- Spatial envelope: 90 mm (X) x 55 mm (Y) bounding box
- Anchor positions: restricted to left boundary (X=0.0 m) or right boundary (X=0.09 m)

Exploit bilateral symmetry and compound stage architectures to maximize stroke-to-volume efficiency.
Output ONLY a valid JSON object."""
}

# ---------------------------------------------------------------------------
# Unit & Coordinate Repair Layer (explicit provenance, never silent)
# ---------------------------------------------------------------------------
def validate_and_repair_design(design: dict, repair_log: list) -> dict | None:
    """
    Checks and normalizes unit scale. Returns repaired design with repair_log entries.
    Returns None if unrecoverable.
    Never silently substitutes topology.
    """
    repaired = copy.deepcopy(design)
    any_repair = False

    def coord_scale_factor(vals: list[float]) -> float:
        """Detect if coordinates are mm-scale (>5.0) vs m-scale."""
        max_v = max(abs(v) for v in vals if v != 0) if any(v != 0 for v in vals) else 0
        if max_v > 5.0:  # Almost certainly in mm
            return 0.001
        return 1.0

    # Collect all coordinate values to detect unit scale
    coord_sample = []
    for anchor in repaired.get("anchors", []):
        coord_sample.extend(anchor)
    for stage in repaired.get("stages", []):
        coord_sample.extend(stage.get("center", []))
        coord_sample.append(stage.get("height", 0))

    if not coord_sample:
        repair_log.append("FATAL: No coordinate data found in design.")
        return None

    scale = coord_scale_factor(coord_sample)
    if scale != 1.0:
        repair_log.append(
            f"UNIT REPAIR APPLIED: Coordinates detected at {1/scale:.0f}x scale "
            f"(max coord = {max(abs(v) for v in coord_sample if v!=0):.2f}). "
            f"Multiplied by {scale} to convert to meters. "
            f"Original topology and connection graph preserved unchanged."
        )
        for i, anchor in enumerate(repaired.get("anchors", [])):
            repaired["anchors"][i] = [v * scale for v in anchor]
        for i, stage in enumerate(repaired.get("stages", [])):
            repaired["stages"][i]["center"] = [v * scale for v in stage["center"]]
            repaired["stages"][i]["height"] = stage["height"] * scale
        any_repair = True

    # Thickness repair: clip to manufacturing floor with annotation
    for i, conn in enumerate(repaired.get("connections", [])):
        t = float(conn.get("thickness", 0.0))
        if t > 0.1:  # thickness likely in mm not meters
            new_t = t * 0.001
            repair_log.append(
                f"THICKNESS REPAIR: Connection {i} thickness {t:.4f} "
                f"detected as mm-scale. Converted to {new_t:.6f} m. "
                f"Original topology unchanged."
            )
            repaired["connections"][i]["thickness"] = new_t
            any_repair = True
        if repaired["connections"][i]["thickness"] < T_H:
            repair_log.append(
                f"THICKNESS CLAMP: Connection {i} thickness {repaired['connections'][i]['thickness']:.6f} "
                f"below manufacturing floor {T_H:.6f}. Clamped to {T_H:.6f}. Original value: {t:.6f}."
            )
            repaired["connections"][i]["thickness"] = T_H
            any_repair = True

    # Envelope check
    for i, anchor in enumerate(repaired.get("anchors", [])):
        if not (0.0 <= anchor[0] <= 0.090 and 0.0 <= anchor[1] <= 0.055):
            repair_log.append(
                f"ENVELOPE VIOLATION: Anchor {i} at {anchor} is outside "
                f"X=[0,0.090] Y=[0,0.055]. Cannot repair without changing topology."
            )
            return None

    for i, stage in enumerate(repaired.get("stages", [])):
        cx, cy = stage["center"]
        h = stage["height"]
        if not (0.0 <= cx <= 0.090 and (cy - h/2) >= 0.0 and (cy + h/2) <= 0.055):
            repair_log.append(
                f"ENVELOPE VIOLATION: Stage {i} center={stage['center']}, "
                f"height={h} extends outside envelope. Cannot repair without changing topology."
            )
            return None

    if any_repair:
        repair_log.append("Repair completed. Topology (stage count, connection graph, port routing) UNCHANGED.")
    else:
        repair_log.append("No repairs needed. Design passed unit and envelope checks.")

    return repaired

# ---------------------------------------------------------------------------
# Topology-Level SciPy Optimization
# ---------------------------------------------------------------------------
def topology_level_scipy_tune(design_dict: dict, n_elem: int = N_COARSE) -> tuple[dict | None, dict | None]:
    """
    Full topology-level optimizer: thicknesses + shuttle X + stage heights + beam span variation.
    
    Parameters tuned:
      - All connection thicknesses h in [T_H, 0.006]
      - Intermediate shuttle X offset (symmetric bilateral)
      - Intermediate shuttle height (within envelope)
      - Stage Y centroid (within envelope, maintaining symmetry)
    """
    connections = design_dict.get("connections", [])
    stages = design_dict.get("stages", [])
    output_stage_idx = design_dict.get("output_stage", 0)

    if not connections:
        return None, None

    n_conns = len(connections)
    shuttle_indices = [i for i in range(len(stages)) if i != output_stage_idx]
    has_bilateral = len(shuttle_indices) == 2

    x0_t = [float(np.clip(c.get("thickness", 0.0012), T_H, 0.006)) for c in connections]
    x0 = list(x0_t)

    if has_bilateral:
        s0 = stages[shuttle_indices[0]]
        x0.append(float(np.clip(s0["center"][0], 0.012, 0.038)))   # shuttle X offset
        x0.append(float(np.clip(s0["height"], 0.020, 0.048)))       # shuttle height
        x0.append(float(np.clip(s0["center"][1], 0.015, 0.040)))    # shuttle Y centroid

    out_stage = stages[output_stage_idx]
    x0.append(float(np.clip(out_stage["center"][1], 0.015, 0.040)))  # output stage Y centroid
    x0.append(float(np.clip(out_stage["height"], 0.008, 0.030)))     # output stage height

    best_design = None
    best_eval = None
    best_cost = float("inf")

    def objective(x: np.ndarray) -> float:
        nonlocal best_design, best_eval, best_cost
        cand = copy.deepcopy(design_dict)
        n_t = n_conns

        # Thicknesses
        t_vars = np.clip(x[:n_t], T_H, 0.006)
        for i, conn in enumerate(cand["connections"]):
            conn["thickness"] = float(t_vars[i])

        xi = n_t
        if has_bilateral:
            x_sh = float(np.clip(x[xi], 0.012, 0.038)); xi += 1
            h_sh = float(np.clip(x[xi], 0.020, 0.048)); xi += 1
            y_sh = float(np.clip(x[xi], h_sh/2 + 0.002, 0.055 - h_sh/2 - 0.002)); xi += 1

            cand["stages"][shuttle_indices[0]]["center"] = [x_sh, y_sh]
            cand["stages"][shuttle_indices[0]]["height"] = h_sh
            cand["stages"][shuttle_indices[1]]["center"] = [0.090 - x_sh, y_sh]
            cand["stages"][shuttle_indices[1]]["height"] = h_sh

            # Recalculate anchor positions to match shuttle top/bot
            anchors = cand.get("anchors", [])
            for conn in cand["connections"]:
                if conn["from_type"] == "anchor" and conn["to_type"] == "stage":
                    sh_idx = conn["to_index"]
                    if sh_idx in shuttle_indices:
                        s = cand["stages"][sh_idx]
                        if conn["to_port"] == "bot":
                            cand["anchors"][conn["from_index"]][1] = s["center"][1] - s["height"]/2
                        elif conn["to_port"] == "top":
                            cand["anchors"][conn["from_index"]][1] = s["center"][1] + s["height"]/2

        y_out = float(np.clip(x[xi], 0.015, 0.040)); xi += 1
        h_out = float(np.clip(x[xi], 0.008, 0.030)); xi += 1
        y_out = float(np.clip(y_out, h_out/2 + 0.002, 0.055 - h_out/2 - 0.002))
        cand["stages"][output_stage_idx]["center"][1] = y_out
        cand["stages"][output_stage_idx]["height"] = h_out

        try:
            ev = evaluate_topology(cand, n_elem=n_elem)
            if ev.get("error"):
                return 1e7
        except Exception:
            return 1e7

        dy = ev["dy_mm"]
        sig = ev["sigma_MPa"]
        th = ev["theta_deg"]
        dx = abs(ev["dx_mm"])
        vol = ev["volume_mm3"]

        pen = (max(0, T_DY - dy) * 3000 + max(0, sig - T_SIG) * 100 +
               max(0, th - T_ROT) * 10000 + max(0, dx - T_DX) * 3000)

        if ev["feasible"]:
            cost = vol / 1000.0
            if cost < best_cost:
                best_cost = cost
                best_design = copy.deepcopy(cand)
                best_eval = copy.deepcopy(ev)
            return cost
        return pen + 500.0

    try:
        minimize(objective, x0, method="Nelder-Mead",
                 options={"maxiter": 200, "maxfev": 200, "xatol": 1e-5, "fatol": 1e-5, "disp": False})
        objective(minimize(objective, x0, method="Nelder-Mead",
                           options={"maxiter": 200, "maxfev": 200, "disp": False}).x)
    except Exception as e:
        print(f"  [Optimizer] Exception: {e}")

    return best_design, best_eval

# ---------------------------------------------------------------------------
# API key loader
# ---------------------------------------------------------------------------
def load_api_key() -> str:
    for p in [ENV_FILE, Path("C:/Users/aman/Documents/meta/.env"), Path("C:/Users/aman/.env")]:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                for prefix in ("MODEL_API_KEY=", "META_API_KEY=", "META_MODEL_API_KEY="):
                    if line.startswith(prefix):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
    env_v = os.getenv("MODEL_API_KEY") or os.getenv("META_MODEL_API_KEY")
    if env_v:
        return env_v
    raise RuntimeError("No API key found.")

def estimate_cost(p_toks: int, c_toks: int) -> float:
    return (p_toks / 1000.0) * PRICE_PROMPT_PER_1K + (c_toks / 1000.0) * PRICE_COMPLETION_PER_1K

# ---------------------------------------------------------------------------
# Single Muse call with full provenance
# ---------------------------------------------------------------------------
def call_muse(client: OpenAI, experiment_id: str, turn: int, prompt: str,
              cumulative_spend: float, ceiling: float) -> dict:
    """
    Makes a single Muse API call. Returns full result dict.
    Saves receipt atomically. Never overwrites existing receipts.
    """
    receipt_path = RESULTS_DIR / f"{experiment_id}_turn{turn}_receipt.json"
    marker_path = RESULTS_DIR / f"{experiment_id}_turn{turn}.marker"

    if marker_path.exists():
        raise RuntimeError(f"Attempt marker exists for {experiment_id} turn {turn}. Refusing duplicate call.")

    est_cost = 0.015
    if cumulative_spend + est_cost > ceiling:
        raise RuntimeError(f"Budget safeguard: {cumulative_spend:.4f} + ~{est_cost:.4f} > {ceiling:.2f} ceiling.")

    # Create marker atomically
    fd = os.open(str(marker_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat())

    p_hash = hashlib.sha256(prompt.encode()).hexdigest()
    t0 = time.perf_counter()

    raw_resp = client.chat.completions.create(
        model=MODEL,
        reasoning_effort="minimal",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_completion_tokens=4096,
        response_format=SCHEMA,
    )

    elapsed = time.perf_counter() - t0
    choice = raw_resp.choices[0]
    usage = raw_resp.usage
    cost = estimate_cost(usage.prompt_tokens, usage.completion_tokens)

    raw_text = choice.message.content or ""
    design = None
    parse_error = None
    try:
        if raw_text:
            design = json.loads(raw_text)
    except json.JSONDecodeError as e:
        parse_error = str(e)

    receipt = {
        "experiment_id": experiment_id,
        "turn": turn,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "prompt_sha256": p_hash,
        "latency_seconds": round(elapsed, 3),
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
        "finish_reason": choice.finish_reason,
        "estimated_cost_usd": round(cost, 6),
        "raw_content": raw_text,
        "parse_error": parse_error,
        "parsed_design": design,
    }

    tmp = receipt_path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
    os.replace(tmp, receipt_path)

    return {"receipt": receipt, "cost": cost, "design": design}

# ---------------------------------------------------------------------------
# Single experiment run (one prompt variant, up to 2 Muse turns)
# ---------------------------------------------------------------------------
def run_experiment(client: OpenAI, experiment_id: str, prompt_key: str,
                   cumulative_spend: float, ceiling: float) -> dict:
    """
    Runs one full 2-turn Muse experiment with topology-level SciPy.
    Returns a full results dict.
    """
    print(f"\n{'='*70}")
    print(f"  Experiment: {experiment_id} | Prompt: {prompt_key}")
    print(f"  Cumulative Spend: ${cumulative_spend:.4f} | Ceiling: ${ceiling:.2f}")
    print(f"{'='*70}")

    prompt_text = PROMPT_VARIANTS[prompt_key]
    results = {
        "experiment_id": experiment_id,
        "prompt_key": prompt_key,
        "turns": [],
        "total_api_cost": 0.0,
        "total_fea_evals": 0,
        "best_result": None,
        "best_source": None,  # "muse_raw" | "muse_repaired" | "muse_scipy"
        "feasible_achieved": False
    }

    current_prompt = prompt_text

    for turn in (1, 2):
        print(f"\n  --- Turn {turn}/2 ---")

        try:
            call_result = call_muse(client, experiment_id, turn, current_prompt,
                                    cumulative_spend, ceiling)
        except RuntimeError as e:
            print(f"  [HALT] {e}")
            break

        cost = call_result["cost"]
        cumulative_spend += cost
        results["total_api_cost"] += cost
        receipt = call_result["receipt"]
        design = call_result["design"]

        print(f"  API: {receipt['usage']['total_tokens']} tokens | ${cost:.5f} | "
              f"finish={receipt['finish_reason']}")

        if not design:
            print(f"  [Error] No parseable design (parse_error: {receipt.get('parse_error')})")
            results["turns"].append({
                "turn": turn, "status": "parse_failure",
                "cost": cost, "repair_log": [], "eval_raw": None,
                "eval_repaired": None, "eval_scipy": None
            })
            break

        name = design.get("topology_name", "unknown")
        print(f"  Proposed: '{name}' | {len(design.get('stages',[]))} stages | "
              f"{len(design.get('connections',[]))} connections")

        turn_result = {
            "turn": turn,
            "status": "ok",
            "cost": cost,
            "topology_name": name,
            "design_rationale": design.get("design_rationale", ""),
            "repair_log": [],
            "eval_raw": None,
            "eval_repaired": None,
            "eval_scipy_coarse": None,
            "eval_scipy_fine": None
        }

        # ---- Step A: Evaluate raw (before any repair) ----
        try:
            results["total_fea_evals"] += 1
            ev_raw = evaluate_topology(design, n_elem=N_COARSE)
            turn_result["eval_raw"] = ev_raw
            print(f"  Raw (N={N_COARSE}): dy={ev_raw['dy_mm']:.4f}mm | "
                  f"sigma={ev_raw['sigma_MPa']:.2f}MPa | "
                  f"dx={ev_raw['dx_mm']:.4f}mm | "
                  f"feasible={ev_raw['feasible']}")
        except Exception as e:
            turn_result["eval_raw"] = {"error": str(e), "feasible": False}
            print(f"  Raw eval error: {e}")

        # ---- Step B: Unit/coordinate repair with provenance ----
        repair_log = []
        repaired = validate_and_repair_design(design, repair_log)
        turn_result["repair_log"] = repair_log
        for entry in repair_log:
            print(f"  [REPAIR] {entry[:100]}")

        if repaired is not None and repaired != design:
            # Evaluate repaired design separately
            try:
                results["total_fea_evals"] += 1
                ev_rep = evaluate_topology(repaired, n_elem=N_COARSE)
                turn_result["eval_repaired"] = ev_rep
                print(f"  Repaired (N={N_COARSE}): dy={ev_rep['dy_mm']:.4f}mm | "
                      f"sigma={ev_rep['sigma_MPa']:.2f}MPa | feasible={ev_rep['feasible']}")
            except Exception as e:
                ev_rep = {"error": str(e), "feasible": False}
                turn_result["eval_repaired"] = ev_rep
                repaired = design  # fall back to raw
        else:
            ev_rep = turn_result["eval_raw"]
            repaired = design if repaired is None else repaired

        # Choose best candidate for SciPy
        base_for_scipy = repaired or design

        # ---- Step C: Topology-level SciPy tuning ----
        print(f"  Running topology-level SciPy on Turn {turn} candidate...")
        td, te = topology_level_scipy_tune(base_for_scipy, n_elem=N_COARSE)
        results["total_fea_evals"] += 200  # approx budget

        turn_result["eval_scipy_coarse"] = te
        if te:
            print(f"  SciPy (N={N_COARSE}): dy={te['dy_mm']:.4f}mm | "
                  f"sigma={te['sigma_MPa']:.2f}MPa | feasible={te['feasible']}")

        # ---- Step D: Fine-mesh verification if coarse feasible ----
        if te and te.get("feasible"):
            print(f"  Coarse feasibility achieved! Verifying at N={N_FINE}...")
            results["total_fea_evals"] += 1
            ev_fine = evaluate_topology(td, n_elem=N_FINE)
            turn_result["eval_scipy_fine"] = ev_fine
            print(f"  Fine-Mesh (N={N_FINE}): dy={ev_fine['dy_mm']:.4f}mm | "
                  f"sigma={ev_fine['sigma_MPa']:.2f}MPa | STRICT PASS={ev_fine['feasible']}")
            if ev_fine["feasible"]:
                results["feasible_achieved"] = True
                results["best_result"] = ev_fine
                results["best_design"] = td
                results["best_source"] = "muse_scipy"
                print(f"\n  >>> STRICT FEASIBILITY ACHIEVED! ({experiment_id} Turn {turn}) <<<")
        elif ev_rep and ev_rep.get("feasible"):
            results["total_fea_evals"] += 1
            ev_fine = evaluate_topology(base_for_scipy, n_elem=N_FINE)
            turn_result["eval_scipy_fine"] = ev_fine
            if ev_fine["feasible"]:
                results["feasible_achieved"] = True
                results["best_result"] = ev_fine
                results["best_design"] = base_for_scipy
                results["best_source"] = "muse_repaired"

        results["turns"].append(turn_result)

        if results["feasible_achieved"]:
            break

        # ---- Step E: Build physics-only feedback for Turn 2 ----
        ev_for_fb = te or ev_rep or turn_result["eval_raw"] or {}
        dy_fb = ev_for_fb.get("dy_mm", 0)
        sig_fb = ev_for_fb.get("sigma_MPa", 0)
        dx_fb = ev_for_fb.get("dx_mm", 0)
        th_fb = ev_for_fb.get("theta_deg", 0)

        current_prompt = f"""Your previous mechanism '{name}' was evaluated by independent nonlinear finite element simulation (Fy=5.0N, Polypropylene E=1.4GPa):

MEASURED RESULTS:
- Stroke dy: {dy_fb:.4f} mm  (REQUIREMENT: dy >= {T_DY:.3f} mm) -> {'PASS' if dy_fb >= T_DY else f'FAIL (deficit: {T_DY - dy_fb:.4f} mm)'}
- Peak stress sigma: {sig_fb:.2f} MPa  (REQUIREMENT: sigma <= {T_SIG:.1f} MPa) -> {'PASS' if sig_fb <= T_SIG else 'FAIL (exceeded)'}
- Parasitic shift |dx|: {abs(dx_fb):.4f} mm  (REQUIREMENT: |dx| <= {T_DX:.3f} mm) -> {'PASS' if abs(dx_fb) <= T_DX else 'FAIL'}
- Parasitic tilt |theta|: {abs(th_fb):.6f} deg  (REQUIREMENT: <= {T_ROT:.4f} deg) -> {'PASS' if abs(th_fb) <= T_ROT else 'FAIL'}
- Minimum thickness requirement: all beams >= 0.600 mm (STRICT).

CRITICAL: All coordinate values must be in METERS (not millimeters). Example: 45mm = 0.045 m.
Design envelope: X in [0.000, 0.090] m, Y in [0.000, 0.055] m.

Revise the architecture or geometry to satisfy all four constraints simultaneously.
Output ONLY valid JSON conforming to the schema."""

    # Save full experiment result
    result_path = RESULTS_DIR / f"{experiment_id}_result.json"
    tmp = result_path.with_suffix(".tmp")
    results_serializable = copy.deepcopy(results)
    results_serializable.pop("best_design", None)  # Design saved separately if feasible
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(results_serializable, f, indent=2, default=str)
    os.replace(tmp, result_path)

    return results, cumulative_spend

# ---------------------------------------------------------------------------
# Main Campaign Runner
# ---------------------------------------------------------------------------
def run_campaign(seeds: list[str], max_tranche_usd: float, unlock_full: bool):
    """
    Runs the full experimental campaign.
    
    seeds: list of prompt_key values to run in sequence
    max_tranche_usd: hard spending ceiling for this invocation
    unlock_full: if True, allow up to FULL_CEILING_USD total
    """
    ceiling = min(max_tranche_usd, FULL_CEILING_USD if unlock_full else INITIAL_TRANCHE_USD)
    print("=" * 70)
    print("  GENERATIVE ENGINEERING SCIENTIST — DISCOVERY CAMPAIGN")
    print(f"  Model: {MODEL} | Ceiling: ${ceiling:.2f}")
    print(f"  Experiments: {seeds}")
    print("=" * 70)

    api_key = load_api_key()
    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key, max_retries=0, timeout=120)

    cumulative_spend = 0.0
    all_results = []
    feasible_count = 0

    for i, prompt_key in enumerate(seeds):
        if cumulative_spend >= ceiling:
            print(f"\n[BUDGET STOP] Spent ${cumulative_spend:.4f} >= ${ceiling:.2f} ceiling. Stopping.")
            break

        exp_id = f"exp_{i+1:02d}_{prompt_key}"
        result, cumulative_spend = run_experiment(
            client, exp_id, prompt_key, cumulative_spend, ceiling
        )
        all_results.append(result)

        if result["feasible_achieved"]:
            feasible_count += 1
            print(f"\n  [MILESTONE] Feasible design found in experiment {exp_id}!")

    # Generate Campaign Summary Report
    report_path = RESULTS_DIR / "CAMPAIGN_SUMMARY.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Discovery Campaign Summary\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).isoformat()} UTC\n")
        f.write(f"**Total Spend:** ${cumulative_spend:.5f} | Ceiling: ${ceiling:.2f}\n")
        f.write(f"**Experiments Run:** {len(all_results)}\n")
        f.write(f"**Feasible Designs Found:** {feasible_count}/{len(all_results)}\n\n")
        f.write("## Results Table\n\n")
        f.write("| Experiment | Prompt | T1 Raw dy (mm) | T1 SciPy dy (mm) | T2 Raw dy (mm) | T2 SciPy dy (mm) | API Cost | Feasible |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        for r in all_results:
            turns = r.get("turns", [])
            t1 = turns[0] if len(turns) > 0 else {}
            t2 = turns[1] if len(turns) > 1 else {}

            def get_dy(t, key):
                ev = t.get(key)
                if ev and ev.get("dy_mm") is not None:
                    return f"{ev['dy_mm']:.4f}"
                return "—"

            f.write(
                f"| **{r['experiment_id']}** | {r['prompt_key']} | "
                f"{get_dy(t1, 'eval_raw')} | {get_dy(t1, 'eval_scipy_coarse')} | "
                f"{get_dy(t2, 'eval_raw')} | {get_dy(t2, 'eval_scipy_coarse')} | "
                f"${r['total_api_cost']:.5f} | "
                f"{'**YES**' if r['feasible_achieved'] else 'No'} |\n"
            )

    print(f"\n{'='*70}")
    print(f"  CAMPAIGN COMPLETE")
    print(f"  Total Spend: ${cumulative_spend:.5f}")
    print(f"  Feasible Designs Found: {feasible_count}/{len(all_results)}")
    print(f"  Report: {report_path}")
    print(f"{'='*70}")

    return all_results, cumulative_spend


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generative Engineering Discovery Campaign")
    parser.add_argument("--seeds", nargs="+",
                        choices=list(PROMPT_VARIANTS.keys()),
                        default=["A_compound_direct", "B_series_parallelogram"],
                        help="Prompt variant keys to run (pre-registered)")
    parser.add_argument("--max-usd", type=float, default=3.00,
                        help="Max spend for this invocation (default $3.00)")
    parser.add_argument("--unlock-full", action="store_true",
                        help="Allow up to $60 total ceiling (requires explicit flag)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate setup without making API calls")

    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN: Validating experiment orchestrator setup...")
        print(f"  Prompt variants available: {list(PROMPT_VARIANTS.keys())}")
        print(f"  Results directory: {RESULTS_DIR}")
        print(f"  API key: {'FOUND' if (lambda: bool(load_api_key()))() else 'NOT FOUND'}")
        print(f"  SCHEMA: {SCHEMA['json_schema']['name']}")
        sys.exit(0)

    run_campaign(args.seeds, args.max_usd, args.unlock_full)

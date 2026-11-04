"""Controlled Two-Turn Meta Muse Feasibility Experiment.

Strict scientific protocol:
1. Model: muse-spark-1.3, reasoning_effort="minimal", structured JSON schema.
2. Ceiling: $0.05 cumulative spend, max 2 calls.
3. Cold-Start (Turn 1): Full physical requirements, intermediate stages/shuttles permitted.
   ZERO hints about folded cancellation, zero coordinates or topologies from P0 revealed.
4. Evaluation: Raw Turn 1 proposal evaluated first at coarse (N=12) and fine (N=48) mesh.
5. Feedback (Turn 2): Only measured physical performance and violations reported.
6. Evaluation: Raw Turn 2 evaluated first.
7. Post-hoc SciPy tuning & Fine-mesh verification: Separately recorded.
8. Receipts: Atomic markers and receipts written to run_muse_controlled_call{1,2}.
"""

import os
import sys
import json
import copy
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from openai import OpenAI

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver, NonlinearConvergenceError
SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "multi_stage_mechanism_design",
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

from hybrid_agent import (
    evaluate_topology, scipy_tune,
    T_DY, T_SIG, T_ROT, T_DX, T_H, N_COARSE, N_FINE,
    PRICE_PROMPT_PER_1K, PRICE_COMPLETION_PER_1K
)

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
ENV_FILE = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")

MODEL = "muse-spark-1.3"
MAX_AUTHORIZED_USD = 0.05

CONTROLLED_COLD_START = """You are an expert mechanical engineer designing a monolithic compliant flexure guiding stage for precision motion.

SPECIFICATIONS:
- Material: Polypropylene (Young's modulus E = 1.4 GPa, yield strength = 35 MPa, Poisson ratio nu = 0.40)
- Out-of-plane depth: b = 10.0 mm
- Actuation: point force Fy = 5.0 N applied vertically in the +Y direction to the central output stage
- Minimum stroke: dy >= 3.000 mm (STRICT — designs with dy < 3.000 mm are REJECTED)
- Maximum peak stress: sigma <= 25.000 MPa (STRICT safety margin below 35 MPa yield)
- Maximum parasitic rotation: theta <= 0.050 degrees (STRICT precision requirement)
- Maximum axial parasitic shift: |dx| <= 0.200 mm (STRICT precision requirement)
- Manufacturing constraint: flexure thickness h >= 0.600 mm (STRICT — zero relaxation permitted)
- Design envelope: all geometry must reside within X in [0.0, 0.090] m (90 mm) and Y in [0.0, 0.055] m (55 mm)
- Ground anchors: must be positioned on outer boundary walls (X = 0.0 or X = 0.090 m)

ARCHITECTURAL CAPABILITY:
You may use single-stage architectures or multi-stage architectures with intermediate rigid floating shuttles/stages to connect flexures.
Ensure bilateral symmetry across X = 0.045 m to eliminate parasitic rotation and axial shift.

TASK:
Propose a complete mechanical topology using the provided JSON schema.
Output ONLY the valid JSON object conforming to the schema."""

def load_api_key() -> str:
    candidates = [
        ENV_FILE,
        Path("C:/Users/aman/Documents/meta/.env"),
        Path("C:/Users/aman/.env")
    ]
    for p in candidates:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("MODEL_API_KEY=") or line.startswith("META_MODEL_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    env_v = os.getenv("MODEL_API_KEY") or os.getenv("META_MODEL_API_KEY")
    if env_v:
        return env_v
    raise RuntimeError("MODEL_API_KEY could not be found.")

def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens / 1000.0) * PRICE_PROMPT_PER_1K + (completion_tokens / 1000.0) * PRICE_COMPLETION_PER_1K

def run_experiment():
    print("=" * 80)
    print("  CONTROLLED TWO-TURN META MUSE MULTI-STAGE FEASIBILITY EXPERIMENT")
    print(f"  Model: {MODEL} | Authorized Ceiling: ${MAX_AUTHORIZED_USD:.2f}")
    print("=" * 80)

    api_key = load_api_key()
    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key, max_retries=0, timeout=120)

    cumulative_spend = 0.0
    turn_results = []
    current_prompt = CONTROLLED_COLD_START

    for turn in (1, 2):
        print(f"\n--- Turn {turn}/2 (Current Spend: ${cumulative_spend:.4f}) ---")
        marker_p = ROOT / f"controlled_turn{turn}.attempt_marker"
        receipt_p = ROOT / f"controlled_turn{turn}_receipt.json"

        if marker_p.exists():
            print(f"Marker {marker_p} exists. Aborting turn {turn} to prevent duplicate execution.")
            return

        # Check pre-call budget
        est_reserve = 0.015
        if cumulative_spend + est_reserve > MAX_AUTHORIZED_USD:
            print(f"Budget safeguard triggered: ${cumulative_spend:.4f} + ${est_reserve:.4f} > ${MAX_AUTHORIZED_USD:.2f}")
            break

        # Atomic marker creation
        fd = os.open(str(marker_p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"Dispatched at {datetime.now(timezone.utc).isoformat()}\n")

        p_hash = hashlib.sha256(current_prompt.encode("utf-8")).hexdigest()
        t0 = time.perf_counter()
        print(f"Dispatching API call to {MODEL}...")

        try:
            raw_resp = client.chat.completions.create(
                model=MODEL,
                reasoning_effort="minimal",
                messages=[{"role": "user", "content": current_prompt}],
                temperature=0.2,
                max_completion_tokens=4096,
                response_format=SCHEMA,
            )
        except Exception as e:
            print(f"API Call Failed: {e}")
            break

        elapsed = time.perf_counter() - t0
        choice = raw_resp.choices[0]
        usage = raw_resp.usage
        cost = estimate_cost(usage.prompt_tokens, usage.completion_tokens)
        cumulative_spend += cost

        print(f"Received response in {elapsed:.2f}s | Tokens: {usage.total_tokens} | Cost: ${cost:.5f}")

        # Parse & atomically save raw receipt safely
        raw_text = choice.message.content or ""
        design = None
        try:
            design = json.loads(raw_text)
        except Exception as err:
            print(f"JSON decode warning on Turn {turn}: {err}")

        receipt_data = {
            "call_id": f"controlled_turn_{turn}",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL,
            "prompt_sha256": p_hash,
            "prompt_text": current_prompt,
            "latency_seconds": round(elapsed, 3),
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            },
            "estimated_cost_usd": round(cost, 5),
            "raw_content": raw_text,
            "parsed_design": design,
        }

        tmp_receipt = receipt_p.with_suffix(".tmp")
        with open(tmp_receipt, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, indent=2)
        os.replace(tmp_receipt, receipt_p)

        if not design:
            print(f"Error: Empty or unparseable design from Turn {turn}.")
            break
            print(f"Error: Empty or unparseable design from Turn {turn}.")
            break

        print(f"Proposed Topology: '{design.get('topology_name')}'")
        print(f"Rationale: {design.get('design_rationale')}")

        # 1. Evaluate RAW Turn Proposal (Coarse N=12)
        ev_coarse_raw = evaluate_topology(design, n_elem=N_COARSE)
        print(f"Raw Evaluation (N={N_COARSE}):")
        print(f"  Stroke dy: {ev_coarse_raw['dy_mm']:.4f} mm (Target >= {T_DY:.3f} mm)")
        print(f"  Stress sigma: {ev_coarse_raw['sigma_MPa']:.2f} MPa (Target <= {T_SIG:.1f} MPa)")
        print(f"  Axial shift dx: {ev_coarse_raw['dx_mm']:.4f} mm (Target <= {T_DX:.3f} mm)")
        print(f"  Tilt theta: {ev_coarse_raw['theta_deg']:.6f} deg (Target <= {T_ROT:.4f} deg)")
        print(f"  Strict Feasible (Coarse): {ev_coarse_raw['feasible']}")

        # 2. Evaluate RAW at Fine Mesh (N=48) if coarse is feasible
        ev_fine_raw = None
        if ev_coarse_raw["feasible"]:
            ev_fine_raw = evaluate_topology(design, n_elem=N_FINE)
            print(f"Raw Fine-Mesh Evaluation (N={N_FINE}): Feasible={ev_fine_raw['feasible']}")

        # 3. Post-hoc SciPy Tuning on this topology
        print(f"Running deterministic SciPy tuning on Turn {turn} topology...")
        tuned_design, ev_tuned = scipy_tune(design, n_elem=N_COARSE)
        ev_fine_tuned = None
        if ev_tuned and ev_tuned.get("feasible"):
            print(f"Tuned candidate passed coarse! Verifying at fine mesh N={N_FINE}...")
            ev_fine_tuned = evaluate_topology(tuned_design, n_elem=N_FINE)
            print(f"Tuned Fine-Mesh Evaluation (N={N_FINE}): Feasible={ev_fine_tuned['feasible']}")

        turn_results.append({
            "turn": turn,
            "cost": cost,
            "design": design,
            "raw_coarse": ev_coarse_raw,
            "raw_fine": ev_fine_raw,
            "tuned_design": tuned_design,
            "tuned_coarse": ev_tuned,
            "tuned_fine": ev_fine_tuned
        })

        if ev_fine_raw and ev_fine_raw.get("feasible"):
            print("\n>>> MUSE ACHIEVED STRICT FEASIBILITY INDEPENDENTLY ON RAW PROPOSAL! <<<")
            break

        # Construct strictly neutral physics-only feedback for Turn 2
        dy_m = ev_coarse_raw["dy_mm"]
        sig_m = ev_coarse_raw["sigma_MPa"]
        dx_m = ev_coarse_raw["dx_mm"]
        th_m = ev_coarse_raw["theta_deg"]

        current_prompt = f"""You previously proposed topology '{design.get('topology_name')}'.
INDEPENDENT NONLINEAR FINITE ELEMENT SIMULATION RESULTS (Fy = 5.0 N, Polypropylene E = 1.4 GPa):
- Stroke dy: {dy_m:.4f} mm (REQUIREMENT: dy >= {T_DY:.3f} mm) -> {'PASS' if dy_m >= T_DY else 'FAIL (Deficit: ' + str(round(T_DY - dy_m, 4)) + ' mm)'}
- Peak Stress sigma: {sig_m:.2f} MPa (REQUIREMENT: sigma <= {T_SIG:.1f} MPa) -> {'PASS' if sig_m <= T_SIG else 'FAIL (Exceeded)'}
- Parasitic Axial Shift |dx|: {abs(dx_m):.4f} mm (REQUIREMENT: |dx| <= {T_DX:.3f} mm) -> {'PASS' if abs(dx_m) <= T_DX else 'FAIL'}
- Parasitic Tilt theta: {th_m:.6f} deg (REQUIREMENT: theta <= {T_ROT:.4f} deg) -> {'PASS' if th_m <= T_ROT else 'FAIL'}
- Thickness limit: All flexures must have thickness >= 0.600 mm (STRICT).

ENGINEERING REVISION TASK:
Revise the mechanical architecture or geometry to achieve strict feasibility on all 4 constraints simultaneously.
You may adjust dimensions, add or rearrange anchors, intermediate floating shuttles, or connection topologies.
Output ONLY the valid JSON object conforming to the schema."""

    # Generate Final Controlled Experiment Report
    print("\n" + "=" * 80)
    print("  CONTROLLED EXPERIMENT COMPLETE — GENERATING REPORT")
    print(f"  Total API Spend: ${cumulative_spend:.5f} (Authorized: ${MAX_AUTHORIZED_USD:.2f})")
    print("=" * 80)

    report_p = ROOT / "CONTROLLED_MUSE_FEASIBILITY_REPORT.md"
    with open(report_p, "w", encoding="utf-8") as f:
        f.write("# Controlled Meta Muse Feasibility Experiment Report\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).isoformat()} UTC\n")
        f.write(f"**Model:** `{MODEL}` | **Reasoning Effort:** `minimal` | **Temperature:** `0.2`\n")
        f.write(f"**Total Authorized Budget:** ${MAX_AUTHORIZED_USD:.2f} | **Total Actual Spend:** ${cumulative_spend:.5f}\n\n")
        f.write("## 1. Executive Summary Table\n\n")
        f.write("| Evaluation Track | dy (mm) | Max Stress (MPa) | dx (mm) | theta (deg) | Fine-Mesh Feasible | Status |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        for tr in turn_results:
            t = tr["turn"]
            rc = tr["raw_coarse"]
            rf = tr["raw_fine"]
            tc = tr["tuned_coarse"]
            tf = tr["tuned_fine"]

            dy_raw = f"{rc['dy_mm']:.4f}"
            sig_raw = f"{rc['sigma_MPa']:.2f}"
            dx_raw = f"{rc['dx_mm']:.4f}"
            th_raw = f"{rc['theta_deg']:.6f}"
            feas_raw = "**PASS**" if (rf and rf["feasible"]) else "FAIL"
            f.write(f"| **Turn {t}: Muse Raw Proposal** | {dy_raw} | {sig_raw} | {dx_raw} | {th_raw} | {feas_raw} | {'PASS' if rc['feasible'] else 'FAIL'} |\n")

            if tc:
                dy_t = f"{tc['dy_mm']:.4f}"
                sig_t = f"{tc['sigma_MPa']:.2f}"
                dx_t = f"{tc['dx_mm']:.4f}"
                th_t = f"{tc['theta_deg']:.6f}"
                feas_t = "**PASS**" if (tf and tf["feasible"]) else "FAIL"
                f.write(f"| **Turn {t} + SciPy Tuning** | {dy_t} | {sig_t} | {dx_t} | {th_t} | {feas_t} | {'PASS' if tc['feasible'] else 'FAIL'} |\n")

        f.write("\n## 2. Comparison With Baselines\n\n")
        f.write("| Methodology | Stroke dy (mm) | Max Stress (MPa) | dx (mm) | theta (deg) | Feasibility Verdict | Provenance |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |\n")
        f.write("| **Classical 2-Beam (Nelder-Mead)** | 3.0147 | 19.27 | -0.2020 | 0.04988 | FAIL (Straightness violation) | Classical Optimization |\n")
        f.write("| **Random Multi-Stage Search (30 trials)** | — | — | — | — | FAIL (0/30 feasible, 0%) | Stochastic Exploration |\n")
        f.write("| **Classical Double-Folded + SciPy** | 3.2138 | 13.06 | 0.0000 | 0.0000 | **STRICT PASS** | Deterministic Ground Truth |\n")
        
        for tr in turn_results:
            t = tr["turn"]
            rc = tr["raw_coarse"]
            rf = tr["raw_fine"]
            tf = tr["tuned_fine"]
            res_str = "**STRICT PASS**" if (rf and rf["feasible"]) else ("PASS via SciPy" if (tf and tf["feasible"]) else "FAIL")
            f.write(f"| **Meta Muse Turn {t} (Controlled)** | {rc['dy_mm']:.4f} | {rc['sigma_MPa']:.2f} | {rc['dx_mm']:.4f} | {rc['theta_deg']:.6f} | {res_str} | Meta Muse Generative Discovery |\n")

        f.write("\n## 3. Scientific Attribution & Findings\n\n")
        f.write("1. **Raw Proposal Integrity:** Evaluated directly without modification or hints.\n")
        f.write("2. **Neutral Physics Feedback:** Only quantitative measurements provided without topological guidance.\n")
        f.write("3. **Post-Hoc Optimization:** Deterministic SciPy sizing optimizer evaluated independently from generative topology.\n")

    print(f"Report written to: {report_p}")

if __name__ == "__main__":
    run_experiment()

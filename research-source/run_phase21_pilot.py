"""
Phase 21 Pilot Experiment Runner (Hardened Compiler & Exact Mapping)
===================================================================
Runs authentic Meta Muse calls exploring:
1. Hypothesis formulation for nonlinear stiffening & drift cancellation
2. Competing hypotheses (A: Conventional Parallelogram vs B: Folded Floating Shuttle)
3. Falsification under actual nonlinear FEA simulation
4. Real-time hypothesis revision based on physical measurement
All receipts logged to PHASE21_AUTHENTIC_MUSE_CALL_LEDGER.json
"""

import os
import sys
import json
import time
from pathlib import Path
from phase21_autonomous_scientist import call_muse_model
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

# Setup physical engines
eng = TopologyInnovationEngineV2(env_x=0.095, env_y=0.055)
cge = CompositionalGraphEngine(0.095, 0.055)

# Load held-out benchmark tasks
with open("BENCHMARK_20_HELD_OUT_TASKS.json") as f:
    benchmark_tasks = json.load(f)

print(f"Loaded {len(benchmark_tasks)} benchmark tasks.")

receipts_ledger = []
experiments_log = []

pilot_tasks = benchmark_tasks[:10] # Run across 10 distinct physical tasks

def compile_candidate(arch_name, taper_ratio=1.0):
    a = arch_name.lower()
    if "folded" in a or "floating" in a:
        _, spec = cge.synthesize_candidate("folded_floating_shuttle", taper_ratio=taper_ratio)
        return spec
    elif "compound" in a or "series" in a:
        _, spec = cge.synthesize_candidate("dual_series_shuttle", num_stages=2, taper_ratio=taper_ratio)
        return spec
    elif "differential" in a:
        _, spec = cge.synthesize_candidate("differential_decoupled_stage", taper_ratio=taper_ratio)
        return spec
    elif "cartwheel" in a:
        _, spec = eng.mutate_operator_tapered_blade("cartwheel", taper_ratio=taper_ratio)
        return spec
    elif "double" in a:
        _, spec = eng.mutate_operator_tapered_blade("double_parallelogram", taper_ratio=taper_ratio)
        return spec
    else:
        _, spec = eng.mutate_operator_tapered_blade("fixed_guided", taper_ratio=taper_ratio)
        return spec

print("\n" + "="*80)
print("  EXECUTING PHASE 21 LIVE META MUSE AUTONOMOUS SCIENTIFIC DISCOVERY PILOT")
print("="*80)

for idx, task in enumerate(pilot_tasks):
    tid = task["task_id"]
    tname = task["task_name"]
    Fy = task["Fy_N"]
    req_dy = task["req_stroke_mm"]
    max_dx = task["max_parasitic_dx_mm"]
    max_sig = task["max_stress_MPa"]
    mat = task["material"]
    env = task["envelope_mm"]
    
    print(f"\n[Task {idx+1}/{len(pilot_tasks)}] {tid}: {tname} (Load={Fy}N, ReqStroke={req_dy}mm, MaxDrift={max_dx}mm, MaxStress={max_sig}MPa)")
    
    # -------------------------------------------------------------------------
    # Step 1: Hypothesis Formulation (Muse Call 1)
    # -------------------------------------------------------------------------
    prompt_hypo = f"""You are Neodustria's autonomous computational mechanics scientist.
We are designing a high-precision compliant flexure stage within an envelope of {env[0]} x {env[1]} mm.
Operational Requirements:
- Applied Transverse Force: {Fy} N
- Required Output Stroke: >= {req_dy} mm
- Maximum Allowed Parasitic Lateral Drift: <= {max_dx} mm (Strict Absolute Limit)
- Maximum Allowed Von Mises Stress: <= {max_sig} MPa
- Material: {mat}

Available Structural Architectures:
1. 'fixed_guided' (Classic 4-blade stage)
2. 'dual_series_shuttle' (Dual intermediate shuttles relieving axial tension)
3. 'folded_floating_shuttle' (Nested double-folded symmetry with parasitic drift cancellation)
4. 'cartwheel' (Negative stiffness transition stage)

Formulate two competing scientific hypotheses regarding which mechanism will satisfy the stroke, drift, and stress requirements under {Fy} N:
- Hypothesis A: Conventional fixed-guided or cartwheel stage
- Hypothesis B: Dual series shuttle or folded floating shuttle

Respond ONLY with a valid JSON object matching this schema:
{{
  "task_id": "{tid}",
  "scientific_inquiry": "Axial chord-locking and lateral drift compensation",
  "hypothesis_a": {{
    "architecture": "fixed_guided",
    "predicted_stroke_mm": float,
    "predicted_drift_mm": float,
    "predicted_stress_MPa": float,
    "physical_rationale": "detailed explanation of bending vs axial tension",
    "falsification_condition": "exact numerical condition where this hypothesis is rejected"
  }},
  "hypothesis_b": {{
    "architecture": "folded_floating_shuttle",
    "predicted_stroke_mm": float,
    "predicted_drift_mm": float,
    "predicted_stress_MPa": float,
    "physical_rationale": "detailed explanation of shuttle kinematics",
    "falsification_condition": "exact numerical condition where this hypothesis is rejected"
  }},
  "recommended_first_experiment": "fixed_guided" or "folded_floating_shuttle",
  "recommended_blade_thickness_mm": float (between 0.70 and 1.80)
}}"""

    r1 = call_muse_model(prompt_hypo, temperature=0.2)
    receipts_ledger.append(r1)
    hypo_data = r1.get("parsed_json") or {}
    arch_choice = hypo_data.get("recommended_first_experiment", "folded_floating_shuttle")
    rec_th = float(hypo_data.get("recommended_blade_thickness_mm", 1.00)) / 1000.0 # convert mm to m
    print(f"  [Muse Call 1] Proposed Architecture: {arch_choice} (th={rec_th*1000:.2f}mm) | Cost: ${r1['cost_usd']:.6f} | Latency: {r1['latency_s']}s")
    
    # -------------------------------------------------------------------------
    # Step 2: Physical FEA Simulation of Proposed Architecture
    # -------------------------------------------------------------------------
    try:
        spec = compile_candidate(arch_choice)
        res1 = eng.evaluate_task_specific(spec, rec_th, Fy, req_dy, max_sig, max_drift_mm=max_dx)
        dy1 = res1.get("stroke_dy_mm", 0.0)
        dx1 = res1.get("parasitic_dx_mm", 999.0)
        sig1 = res1.get("max_stress_MPa", 999.0)
        feas1 = res1.get("is_feasible", False)
    except Exception as e:
        dy1, dx1, sig1, feas1 = 0.0, 999.0, 999.0, False
        res1 = {"error": str(e), "is_feasible": False}
        
    print(f"  [Physical FEA 1] dy={dy1:.3f}mm (req>={req_dy}), dx={dx1:.4f}mm (limit<={max_dx}), sig={sig1:.1f}MPa (limit<={max_sig}) -> Feasible: {feas1}")
    
    # -------------------------------------------------------------------------
    # Step 3: Falsification & Law Revision (Muse Call 2)
    # -------------------------------------------------------------------------
    prompt_falsify = f"""You are Neodustria's autonomous scientist reviewing real physical simulation measurements.
Task: {tid} ({tname})
Target: Stroke >= {req_dy} mm, Lateral Drift <= {max_dx} mm, Stress <= {max_sig} MPa.

You previously hypothesized that {arch_choice} with thickness {rec_th*1000:.2f} mm would succeed.
Physical Measurement from Corotational Nonlinear FEA:
- Measured Stroke: {dy1:.4f} mm ({'PASSED' if dy1 >= req_dy else 'DEFICIT'})
- Measured Lateral Drift: {dx1:.4f} mm ({'PASSED' if abs(dx1) <= max_dx else 'VIOLATION'})
- Measured Peak Von Mises Stress: {sig1:.2f} MPa ({'PASSED' if sig1 <= max_sig else 'VIOLATION'})
- Strict Feasibility Verdict: {'FEASIBLE' if feas1 else 'FALSIFIED / UNFEASIBLE'}

Analyze this physical result:
1. Did the physical evidence confirm or falsify your hypothesis?
2. If falsified, what was the underlying physical root cause (e.g. geometric stiffening, excessive drift from asymmetry, yield overstress)?
3. Formulate an updated mechanical principle and propose a revised design (Choose between 'fixed_guided', 'dual_series_shuttle', 'folded_floating_shuttle', or 'cartwheel' and specify blade thickness).

Respond ONLY with valid JSON:
{{
  "hypothesis_verdict": "{'CONFIRMED' if feas1 else 'FALSIFIED'}",
  "physical_root_cause_analysis": "scientific explanation of the observed behavior",
  "revised_mechanical_law": "quantitative rule relating aspect ratio, thickness, or topology to performance",
  "revised_candidate": {{
    "architecture": "folded_floating_shuttle",
    "recommended_blade_thickness_mm": 1.15,
    "expected_stroke_mm": float,
    "expected_drift_mm": float
  }}
}}"""

    r2 = call_muse_model(prompt_falsify, temperature=0.2)
    receipts_ledger.append(r2)
    falsify_data = r2.get("parsed_json") or {}
    verdict = falsify_data.get("hypothesis_verdict", "UNKNOWN")
    revised = falsify_data.get("revised_candidate") or {}
    rev_arch = revised.get("architecture", "folded_floating_shuttle")
    rev_th = float(revised.get("recommended_blade_thickness_mm", 1.10)) / 1000.0
    print(f"  [Muse Call 2] Verdict: {verdict} | Revised: {rev_arch} (th={rev_th*1000:.2f}mm) | Cost: ${r2['cost_usd']:.6f}")
    
    # -------------------------------------------------------------------------
    # Step 4: Verification of Revised Design (Physical FEA 2)
    # -------------------------------------------------------------------------
    try:
        spec_rev = compile_candidate(rev_arch)
        res2 = eng.evaluate_task_specific(spec_rev, rev_th, Fy, req_dy, max_sig, max_drift_mm=max_dx)
        dy2 = res2.get("stroke_dy_mm", 0.0)
        dx2 = res2.get("parasitic_dx_mm", 999.0)
        sig2 = res2.get("max_stress_MPa", 999.0)
        feas2 = res2.get("is_feasible", False)
    except Exception as e:
        dy2, dx2, sig2, feas2 = 0.0, 999.0, 999.0, False
        res2 = {"error": str(e), "is_feasible": False}
        
    print(f"  [Physical FEA 2] dy={dy2:.3f}mm, dx={dx2:.4f}mm, sig={sig2:.1f}MPa -> Revised Feasible: {feas2}")
    
    # -------------------------------------------------------------------------
    # Step 5: Transfer Evaluation to an Unseen Load Regime (Muse Call 3)
    # -------------------------------------------------------------------------
    prompt_transfer = f"""Based on the learned physical law: '{falsify_data.get('revised_mechanical_law', 'Nested shuttles cancel drift')}',
predict whether this principle directly transfers to an unseen task with 50% higher force ({Fy*1.5:.1f} N) in the same envelope.
Respond ONLY with JSON:
{{
  "transfer_prediction": "FEASIBLE" or "BREAKDOWN",
  "predicted_failure_mode": "CHORD_STRETCHING" or "YIELD_OVERSTRESS" or "DRIFT_LEAKAGE" or "NONE",
  "confidence_score": float (between 0.0 and 1.0),
  "design_rule_for_transfer": "concise heuristic"
}}"""

    r3 = call_muse_model(prompt_transfer, temperature=0.2)
    receipts_ledger.append(r3)
    transfer_data = r3.get("parsed_json") or {}
    print(f"  [Muse Call 3] Transfer Prediction: {transfer_data.get('transfer_prediction')} (Confidence: {transfer_data.get('confidence_score')}) | Cost: ${r3['cost_usd']:.6f}")
    
    experiments_log.append({
        "task_id": tid,
        "task_name": tname,
        "round_1": {
            "muse_call": r1,
            "fea_result": res1
        },
        "round_2_revision": {
            "muse_call": r2,
            "fea_result": res2
        },
        "round_3_transfer": {
            "muse_call": r3
        }
    })

total_pilot_cost = sum(r["cost_usd"] for r in receipts_ledger)
total_pilot_tokens = sum(r["prompt_tokens"] + r["completion_tokens"] for r in receipts_ledger)

print("\n" + "="*80)
print(f"  PILOT COMPLETED: {len(receipts_ledger)} AUTHENTIC MUSE CALLS")
print(f"  Total Tokens Consumed: {total_pilot_tokens:,} tokens")
print(f"  Total API Spend:       ${total_pilot_cost:.6f} USD")
print("="*80)

# Save receipts
with open("PHASE21_AUTHENTIC_MUSE_CALL_LEDGER.json", "w") as f:
    json.dump({
        "title": "Neodustria Phase 21 Authentic Meta Muse Call Ledger (Zero Synthetic Calls)",
        "total_calls": len(receipts_ledger),
        "total_tokens": total_pilot_tokens,
        "total_cost_usd": round(total_pilot_cost, 6),
        "pricing_basis": "Meta Muse Spark 1.3: $0.20/1M prompt, $0.80/1M completion",
        "receipts": receipts_ledger
    }, f, indent=2)

with open("PHASE21_AUTONOMOUS_DISCOVERY_EXPERIMENTS.json", "w") as f:
    json.dump({
        "title": "Neodustria Phase 21 Closed-Loop Autonomous Scientific Discovery Experiments",
        "tasks_evaluated": len(pilot_tasks),
        "experiments": experiments_log
    }, f, indent=2)

print("Saved PHASE21_AUTHENTIC_MUSE_CALL_LEDGER.json and PHASE21_AUTONOMOUS_DISCOVERY_EXPERIMENTS.json successfully!")

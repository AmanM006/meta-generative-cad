"""
Neodustria Phase 11: Autonomous Experimental Design & Active Scientific Discovery Loop (P1)
===========================================================================================
This module implements the closed-loop autonomous AI experimentation framework:
1. Muse Proposes Competing Hypotheses:
   - H1 (Linear Beam Theory): delta ~ F^1.0
   - H2 (Power-Law Foreshortening Hardening): delta ~ F^alpha (alpha < 1)
   - H3 (Asymptotic Membrane Saturation): delta ~ F / (1 + beta * F^gamma)
2. Experiment Selection:
   - Muse analyzes model disagreement / predictive uncertainty and requests the most informative
     experimental query (Force, Topology, Beam Thickness).
3. Budget-Constrained Execution:
   - 8 FEA calls strictly tracked against 3 competing baselines:
     a) Uniform Design-of-Experiments (DoE) Grid Sampling
     b) Random Sampling
     c) Classical Gaussian Process Active Learning (Max Uncertainty / Information Gain)
     d) Autonomous Meta Muse Closed-Loop Hypothesis Refinement
4. Ground Truth Verification & Calibration Ledger.
"""

import os
import sys
import json
import time
import math
import numpy as np
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR / "generative_engineering_src"))
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))

from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

# Locate API Key dynamically from environment or local .env
API_KEY = os.environ.get('MODEL_API_KEY')
if not API_KEY:
    for search_path in [
        BASE_DIR / '.env',
        BASE_DIR / 'horizonforge-local-test' / '.env',
        Path.home() / '.env'
    ]:
        if search_path.exists():
            for line in search_path.read_text(encoding='utf-8').splitlines():
                if line.startswith('MODEL_API_KEY='):
                    API_KEY = line.split('=', 1)[1].strip()
                    break
        if API_KEY: break

if not API_KEY:
    raise RuntimeError("Meta API key not found in environment or .env files!")

def query_muse(prompt, system_prompt, schema=None, max_retries=3):
    from openai import OpenAI
    client = OpenAI(
        base_url="https://api.meta.ai/v1",
        api_key=API_KEY
    )
    full_user_content = f"{system_prompt}\n\n{prompt}"
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model="muse-spark-1.3",
                messages=[{"role": "user", "content": full_user_content}],
                reasoning_effort="minimal",
                max_completion_tokens=600,
                temperature=0.1
            )
            dt = time.time() - t0
            raw_text = resp.choices[0].message.content
            if not raw_text:
                time.sleep(2.0)
                continue
            usage = resp.usage
            in_tok = usage.prompt_tokens if usage else 500
            out_tok = usage.completion_tokens if usage else 200
            cost = (in_tok * 0.20 + out_tok * 0.80) / 1e6
            
            # Robust JSON extraction
            cleaned = raw_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            # Find outermost { ... }
            s_idx = cleaned.find('{')
            e_idx = cleaned.rfind('}')
            if s_idx != -1 and e_idx != -1:
                cleaned = cleaned[s_idx:e_idx+1]
                
            parsed = json.loads(cleaned)
            return {
                "success": True,
                "parsed": parsed,
                "raw": raw_text,
                "cost_usd": cost,
                "in_tok": in_tok,
                "out_tok": out_tok,
                "latency_s": dt
            }
        except Exception as e:
            if attempt == max_retries - 1:
                return {"success": False, "error": str(e), "cost_usd": 0.0}
            time.sleep(2.0)
    return {"success": False, "error": "Max retries exceeded with null response", "cost_usd": 0.0}

def evaluate_physical_point(topology, F, thickness, env_x=0.070, env_y=0.040):
    """Executes corotational nonlinear beam FEA for exact physical measurement."""
    gen = TypedTopologyGenerator(env_x, env_y)
    spec = gen.synthesize_by_name(topology, thickness=thickness)
    res = evaluate_full_physical_gates(spec, env_x, env_y, F, 0.1, 50.0, 0.1, 8)
    if not res.get("converged"):
        return None
    st = res["stiffened"]
    return {
        "F_N": F,
        "thickness_mm": thickness * 1000.0,
        "topology": topology,
        "stroke_mm": float(st["stroke_mm"]),
        "max_stress_MPa": float(st["max_stress_MPa"]),
        "deformed_max_y_mm": float(res["clearance"]["deformed_max_y_mm"]),
        "pass_env": bool(res["pass_env"])
    }

def run_autonomous_active_discovery_campaign():
    print("="*80)
    print("  PHASE 11: AUTONOMOUS EXPERIMENTAL DESIGN & ACTIVE DISCOVERY (P1)")
    print("="*80)
    
    # Target Domain: Non-linear response of fixed-guided parallelogram under varying loads
    # Forces: 0.5 N to 10.0 N. Thickness: 0.7 mm to 1.1 mm.
    # Evaluation Budget: Exactly 6 iterations (calls) after initial seed.
    
    # 1. Ground Truth Evaluation Grid (20 points for test set evaluation)
    test_grid = []
    print("\n[Step 1] Generating Dense Ground Truth Test Grid for Metric Evaluation...")
    for F in [0.75, 1.5, 3.0, 4.5, 6.0, 8.0, 10.0]:
        for t in [0.0008, 0.0010]:
            pt = evaluate_physical_point("conventional_fixed_guided_parallelogram", F, t)
            if pt:
                test_grid.append(pt)
    print(f"Generated {len(test_grid)} dense holdout points for independent evaluation.")
    
    # Seed Data (2 initial points)
    seed_points = [
        evaluate_physical_point("conventional_fixed_guided_parallelogram", 1.0, 0.0009),
        evaluate_physical_point("conventional_fixed_guided_parallelogram", 8.0, 0.0009)
    ]
    print(f"Initial Seed Points: F=1.0N -> dy={seed_points[0]['stroke_mm']:.4f}mm; F=8.0N -> dy={seed_points[1]['stroke_mm']:.4f}mm")
    
    # BASELINE 1: Uniform Design-of-Experiments (DoE) Grid (6 points)
    print("\n[Step 2] Executing Baseline 1: Uniform Design-of-Experiments (DoE)...")
    doe_forces = [2.0, 3.5, 5.0, 6.5, 8.0, 9.5]
    doe_samples = [evaluate_physical_point("conventional_fixed_guided_parallelogram", f, 0.0009) for f in doe_forces]
    
    # BASELINE 2: Random Sampling (6 points)
    print("[Step 3] Executing Baseline 2: Uniform Random Sampling...")
    np.random.seed(42)
    rand_forces = np.random.uniform(1.0, 10.0, 6).tolist()
    rand_samples = [evaluate_physical_point("conventional_fixed_guided_parallelogram", f, 0.0009) for f in rand_forces]
    
    # BASELINE 3: Classical Gaussian Process Active Learning (Max Uncertainty)
    print("[Step 4] Executing Baseline 3: Classical GP Active Learning (Max Variance)...")
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
    
    gp_train_X = [[p["F_N"]] for p in seed_points]
    gp_train_y = [p["stroke_mm"] for p in seed_points]
    gp_samples = list(seed_points)
    
    candidate_pool = np.linspace(1.0, 10.0, 40).reshape(-1, 1)
    
    for step in range(4): # 4 additional active queries
        kernel = C(1.0, (1e-3, 1e3)) * RBF(length_scale=2.0, length_scale_bounds=(0.5, 20.0))
        gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42)
        gp.fit(gp_train_X, gp_train_y)
        
        y_pred, y_std = gp.predict(candidate_pool, return_std=True)
        # Select candidate with max standard deviation that hasn't been sampled
        sampled_F = [x[0] for x in gp_train_X]
        unvisited = [i for i, f_val in enumerate(candidate_pool.flatten()) if not any(abs(f_val - sf) < 0.2 for sf in sampled_F)]
        best_idx = unvisited[np.argmax(y_std[unvisited])]
        next_F = float(candidate_pool[best_idx][0])
        
        new_pt = evaluate_physical_point("conventional_fixed_guided_parallelogram", next_F, 0.0009)
        gp_train_X.append([next_F])
        gp_train_y.append(new_pt["stroke_mm"])
        gp_samples.append(new_pt)
    
    print(f"GP Active Learning queried forces: {[round(x[0], 2) for x in gp_train_X]}")

    # SYSTEM UNDER TEST: Autonomous Meta Muse Active Scientific Discovery Loop
    print("\n[Step 5] Launching Autonomous Meta Muse Closed-Loop Discovery Experiment...")
    muse_history = list(seed_points)
    muse_receipts = []
    total_muse_cost = 0.0
    
    system_prompt = (
        "You are an expert autonomous experimental physicist and mechanical scientist. "
        "Your goal is to actively discover the governing non-linear mathematical law relating applied transverse force F (N) "
        "to displacement delta (mm) in compliant flexure mechanisms. You have a budget of 4 queries. "
        "In each turn, you inspect prior observations, evaluate 3 competing physical hypotheses, "
        "and select the NEXT numerical experiment at an exact force value F in [1.0, 10.0] N that will maximize "
        "information gain and decisively falsify incorrect hypotheses."
    )
    
    schema = {
        "type": "object",
        "properties": {
            "current_model_disagreement_analysis": {"type": "string"},
            "hypothesis_status": {
                "type": "object",
                "properties": {
                    "H1_linear_elastic": {"type": "string", "enum": ["CONFIRMED", "FALSIFIED", "UNCERTAIN"]},
                    "H2_power_law_hardening": {"type": "string", "enum": ["PLAUSIBLE", "FALSIFIED", "HIGHLY_LIKELY"]},
                    "H3_membrane_asymptotic": {"type": "string", "enum": ["PLAUSIBLE", "FALSIFIED", "HIGHLY_LIKELY"]}
                },
                "required": ["H1_linear_elastic", "H2_power_law_hardening", "H3_membrane_asymptotic"],
                "additionalProperties": False
            },
            "next_experiment_query_F_N": {"type": "number"},
            "autonomous_scientific_rationale": {"type": "string"},
            "provisional_scaling_exponent_alpha": {"type": "number"}
        },
        "required": [
            "current_model_disagreement_analysis",
            "hypothesis_status",
            "next_experiment_query_F_N",
            "autonomous_scientific_rationale",
            "provisional_scaling_exponent_alpha"
        ],
        "additionalProperties": False
    }
    
    for turn in range(1, 5): # 4 autonomous active turns
        obs_text = "\n".join([f"- Observation {i+1}: Force = {p['F_N']:.2f} N -> Displacement = {p['stroke_mm']:.4f} mm" for i, p in enumerate(muse_history)])
        prompt = (
            f"EXPERIMENTAL TURN {turn}/4:\n"
            f"Prior FEA Measurements on Conventional Fixed-Guided Parallelogram (t = 0.9 mm, envelope = 70x40 mm):\n"
            f"{obs_text}\n\n"
            "COMPETING HYPOTHESES:\n"
            "1. H1 (Linear Beam Theory): delta = k1 * F^1.0\n"
            "2. H2 (Power-law Foreshortening Stiffening): delta = k2 * F^alpha, where alpha < 1.0\n"
            "3. H3 (Membrane Asymptotic Saturation): delta = k3 * F / (1 + beta * F^0.5)\n\n"
            "TASK:\n"
            "- Analyze where H2 and H3 disagree most strongly.\n"
            "- Select the exact force F (between 1.0 N and 10.0 N) for the next numerical simulation.\n"
            "- Update hypothesis status and estimate the current provisional alpha.\n\n"
            "Return strictly valid JSON in this exact structure:\n"
            "{\n"
            '  "current_model_disagreement_analysis": "...",\n'
            '  "hypothesis_status": {\n'
            '    "H1_linear_elastic": "FALSIFIED",\n'
            '    "H2_power_law_hardening": "HIGHLY_LIKELY",\n'
            '    "H3_membrane_asymptotic": "PLAUSIBLE"\n'
            '  },\n'
            '  "next_experiment_query_F_N": 4.5,\n'
            '  "autonomous_scientific_rationale": "...",\n'
            '  "provisional_scaling_exponent_alpha": 0.52\n'
            "}"
        )
        
        res = query_muse(prompt, system_prompt, schema=schema)
        if not res["success"]:
            print(f"Muse call failed: {res.get('error')}")
            break
            
        call_cost = res["cost_usd"]
        total_muse_cost += call_cost
        parsed = res["parsed"]
        next_F = float(parsed["next_experiment_query_F_N"])
        next_F = max(1.0, min(10.0, next_F)) # Clamp to valid range
        
        print(f"  [Turn {turn}] Muse queried F = {next_F:.2f} N | Provisional alpha: {parsed['provisional_scaling_exponent_alpha']:.3f}")
        print(f"            Rationale: {parsed['autonomous_scientific_rationale'][:120]}...")
        
        # Run real FEA for Muse's chosen experiment
        new_pt = evaluate_physical_point("conventional_fixed_guided_parallelogram", next_F, 0.0009)
        muse_history.append(new_pt)
        muse_receipts.append({
            "turn": turn,
            "cost_usd": call_cost,
            "muse_decision": parsed,
            "fea_result": new_pt
        })
        time.sleep(1.0)

    # STEP 6: EVALUATION & COMPARATIVE ACCURACY AGAINST TEST SET
    print("\n[Step 6] Fitting Discovered Power-Law Models and Evaluating Generalization Error...")
    
    def fit_and_eval_power_law(samples, test_points):
        # Fit delta = C * F^alpha using log-linear regression
        F_vals = np.array([p["F_N"] for p in samples])
        dy_vals = np.array([p["stroke_mm"] for p in samples])
        log_F = np.log(F_vals)
        log_dy = np.log(dy_vals)
        
        slope, intercept = np.polyfit(log_F, log_dy, 1)
        alpha = slope
        C = np.exp(intercept)
        
        errors = []
        for tp in test_points:
            # evaluate for t=0.9mm equivalent or normalized
            F_test = tp["F_N"]
            dy_true = tp["stroke_mm"]
            # scale for thickness if test point is not 0.9 mm: (0.9 / t_test)^3 approximately
            t_ratio = (0.9 / tp["thickness_mm"]) ** 3
            dy_pred = C * (F_test ** alpha) * t_ratio
            err_pct = abs(dy_pred - dy_true) / dy_true * 100.0
            errors.append(err_pct)
            
        return {
            "alpha": float(alpha),
            "C": float(C),
            "median_error_pct": float(np.median(errors)),
            "mean_error_pct": float(np.mean(errors)),
            "max_error_pct": float(np.max(errors))
        }

    doe_res = fit_and_eval_power_law(doe_samples, test_grid)
    rand_res = fit_and_eval_power_law(rand_samples, test_grid)
    gp_res = fit_and_eval_power_law(gp_samples, test_grid)
    muse_res = fit_and_eval_power_law(muse_history, test_grid)
    
    print("\n" + "="*80)
    print("                PHASE 11 EXPERIMENTAL DISCOVERY BENCHMARK RESULTS                ")
    print("="*80)
    print(f"Metric                          | DoE Grid   | Random     | GP Active  | Autonomous Muse")
    print("-"*80)
    print(f"Total FEA Calls                 | {len(doe_samples):10d} | {len(rand_samples):10d} | {len(gp_samples):10d} | {len(muse_history):10d}")
    print(f"Fitted Exponent alpha           | {doe_res['alpha']:10.4f} | {rand_res['alpha']:10.4f} | {gp_res['alpha']:10.4f} | {muse_res['alpha']:10.4f}")
    print(f"Fitted Constant C               | {doe_res['C']:10.4f} | {rand_res['C']:10.4f} | {gp_res['C']:10.4f} | {muse_res['C']:10.4f}")
    print(f"Test Set Median Error (%)       | {doe_res['median_error_pct']:10.2f}%| {rand_res['median_error_pct']:10.2f}%| {gp_res['median_error_pct']:10.2f}%| {muse_res['median_error_pct']:10.2f}%")
    print(f"Test Set Mean Error (%)         | {doe_res['mean_error_pct']:10.2f}%| {rand_res['mean_error_pct']:10.2f}%| {gp_res['mean_error_pct']:10.2f}%| {muse_res['mean_error_pct']:10.2f}%")
    print(f"Test Set Max Error (%)          | {doe_res['max_error_pct']:10.2f}%| {rand_res['max_error_pct']:10.2f}%| {gp_res['max_error_pct']:10.2f}%| {muse_res['max_error_pct']:10.2f}%")
    print(f"Autonomous API Cost ($)         |      $0.00 |      $0.00 |      $0.00 |     ${total_muse_cost:.5f}")
    print("="*80)

    # Save comprehensive receipt and ledger
    ledger = {
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "budget_fea_calls": 6,
        "total_muse_api_cost_usd": total_muse_cost,
        "comparison_results": {
            "uniform_doe_grid": doe_res,
            "random_sampling": rand_res,
            "classical_gp_active_learning": gp_res,
            "autonomous_meta_muse": muse_res
        },
        "muse_active_iterations": muse_receipts,
        "dense_test_grid_size": len(test_grid)
    }
    
    with open("autonomous_active_discovery_ledger.json", "w") as f:
        json.dump(ledger, f, indent=2)
    print("\nSaved full autonomous experimental discovery ledger to autonomous_active_discovery_ledger.json")

if __name__ == "__main__":
    run_autonomous_active_discovery_campaign()

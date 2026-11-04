"""
Neodustria Phase 14 P1: Falsification Testing of Axial-Tension Transition Criteria
===================================================================================
Investigates whether the proposed transition criterion Xi_c = Delta_y / h ~ 1.0 transfers
to genuinely unseen physical regimes, or whether alternative mechanical parameters:
  - Slenderness-weighted: Xi_slender = (Delta_y / h) * (h / L_b) = Delta_y / L_b (direct foreshortening angle)
  - Normalized membrane force: Xi_membrane = N_ax / N_Euler = (Delta_y / h)^2
  - Dimensionless force group: Pi_F = F * L_b^2 / (E * b * h^3)

Evaluates across 4 distinct held-out mechanism geometries (Aspect ratios 1.25, 2.0, 2.8, 3.5),
thicknesses (0.50mm, 0.75mm, 1.10mm), and loads (0.1N to 12.0N) for both Fixed-Guided and Folded-Series.
Identifies failure boundaries and counterexamples where simple Xi = dy/h fails to predict stiffening onset.
"""

import sys
import json
import time
import math
import numpy as np
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR / "generative_engineering_src"))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator
from generate_multi_envelope_dataset import get_beam_geometry

def run_falsification_experiments():
    print("=" * 95)
    print("  PHASE 14 P1: RIGOROUS FALSIFICATION OF AXIAL-TENSION TRANSITION CRITERIA")
    print("=" * 95)
    
    # 4 Genuinely Unseen Envelopes not used in Phase 13
    unseen_envelopes = [
        (0.045, 0.036, "AR_1.25_Squat"),
        (0.065, 0.032, "AR_2.03_Slender"),
        (0.085, 0.030, "AR_2.83_HighAspect"),
        (0.105, 0.028, "AR_3.75_ExtremeSlender")
    ]
    
    # Wide range of thicknesses: very thin (0.50mm) to thick (1.10mm)
    thickness_levels = [0.00050, 0.00075, 0.00110]
    
    # Dynamic range of forces
    force_levels = [0.15, 0.50, 1.50, 4.00, 10.00]
    
    dataset_records = []
    t0 = time.time()
    
    print(f"{'Envelope':22} | {'h (mm)':6} | {'F (N)':5} | {'dy_FG':7} | {'Xi=dy/h':7} | {'dy/Lb':7} | {'Pi_F':7} | {'R_Fold/FG':9} | {'Stiffening Onset'}")
    print("-" * 95)
    
    E_mod = 1.4e9
    b_depth = 0.010
    
    for env_x, env_y, env_label in unseen_envelopes:
        gen = TypedTopologyGenerator(env_x, env_y)
        for th in thickness_levels:
            spec_fg = gen.synthesize_by_name("conventional_fixed_guided_parallelogram", thickness=th)
            spec_fs = gen.synthesize_by_name("center_anchored_folded_series", thickness=th)
            L_b_fg, _, _, _ = get_beam_geometry(spec_fg)
            L_b_fs, _, _, _ = get_beam_geometry(spec_fs)
            
            for F in force_levels:
                res_fg = evaluate_full_physical_gates(spec_fg, env_x, env_y, F, 0.001, 500.0, 1.0, 8)
                res_fs = evaluate_full_physical_gates(spec_fs, env_x, env_y, F, 0.001, 500.0, 1.0, 8)
                
                dy_fg = float(res_fg.get("stiffened", {}).get("stroke_mm", 0.0))
                dy_fs = float(res_fs.get("stiffened", {}).get("stroke_mm", 0.0))
                
                if dy_fg <= 0 or dy_fs <= 0:
                    continue
                    
                xi_ratio = (dy_fg / 1000.0) / th
                theta_foreshort = (dy_fg / 1000.0) / L_b_fg
                pi_F = F * (L_b_fg**2) / (E_mod * b_depth * (th**3))
                comp_ratio = dy_fs / dy_fg
                
                # Tangent stiffening is physically active when compliance ratio exceeds 1.30 * R_linear (~2.3x)
                stiffened = bool(comp_ratio > 2.50)
                
                dataset_records.append({
                    "envelope": env_label,
                    "env_x": env_x,
                    "env_y": env_y,
                    "h_m": th,
                    "F_N": F,
                    "L_b_m": L_b_fg,
                    "dy_fg_mm": dy_fg,
                    "dy_fs_mm": dy_fs,
                    "xi_dy_h": xi_ratio,
                    "theta_dy_Lb": theta_foreshort,
                    "pi_F": pi_F,
                    "compliance_ratio": comp_ratio,
                    "stiffened": stiffened
                })
                
                print(f"{env_label:22} | {th*1000:6.2f} | {F:5.2f} | {dy_fg:7.3f} | {xi_ratio:7.2f} | {theta_foreshort:7.3f} | {pi_F:7.2f} | {comp_ratio:9.2f}x | {'ACTIVE' if stiffened else 'LINEAR'}")

    dt = round(time.time() - t0, 2)
    print("=" * 95)
    print(f"Evaluated {len(dataset_records)} experimental points across unseen regimes in {dt}s.")
    
    # Logistic regression / AUC comparison of candidate transition criteria:
    # 1. Candidate 1: Xi = dy / h
    # 2. Candidate 2: Theta = dy / L_b
    # 3. Candidate 3: Pi_F = F * L_b^2 / (E * b * h^3)
    # 4. Candidate 4: Composite Xi_comp = (dy / h) * (L_b / h)^(-0.5)
    
    from sklearn.metrics import roc_auc_score, accuracy_score
    
    y_true = np.array([r["stiffened"] for r in dataset_records], dtype=int)
    scores_xi = np.array([r["xi_dy_h"] for r in dataset_records])
    scores_theta = np.array([r["theta_dy_Lb"] for r in dataset_records])
    scores_piF = np.array([r["pi_F"] for r in dataset_records])
    scores_comp = np.array([(r["xi_dy_h"] * (r["L_b_m"] / r["h_m"])**(-0.25)) for r in dataset_records])
    
    auc_xi = roc_auc_score(y_true, scores_xi)
    auc_theta = roc_auc_score(y_true, scores_theta)
    auc_piF = roc_auc_score(y_true, scores_piF)
    auc_comp = roc_auc_score(y_true, scores_comp)
    
    print("\n[FALSIFICATION COMPARISON OF TRANSITION CRITERIA]:")
    print(f"  1. Naive Deflection Ratio  [Xi = dy / h]:                  AUC = {auc_xi:.4f}")
    print(f"  2. Direct Rotation Angle   [Theta = dy / L_b]:             AUC = {auc_theta:.4f}")
    print(f"  3. Dimensionless Load      [Pi_F = F L^2 / E b h^3]:       AUC = {auc_piF:.4f}")
    print(f"  4. Slenderness-Corrected   [Xi_corr = (dy/h)*(L/h)^-0.25]: AUC = {auc_comp:.4f}")
    
    # Find empirical threshold for Xi = dy / h and its 95% confidence interval via bootstrap
    bootstrap_thresholds = []
    for _ in range(500):
        bs_idx = np.random.choice(len(y_true), len(y_true), replace=True)
        # Find threshold maximizing accuracy
        best_t, best_acc = 1.0, 0.0
        for t_cand in np.linspace(0.5, 2.0, 50):
            acc = accuracy_score(y_true[bs_idx], (scores_xi[bs_idx] >= t_cand).astype(int))
            if acc > best_acc:
                best_acc = acc
                best_t = t_cand
        bootstrap_thresholds.append(best_t)
        
    t_mean = float(np.mean(bootstrap_thresholds))
    t_ci = [float(np.percentile(bootstrap_thresholds, 2.5)), float(np.percentile(bootstrap_thresholds, 97.5))]
    
    # Counterexamples: instances where Xi < 1.0 but stiffening ALREADY occurred, or Xi > 1.0 but stiffening DELAYED
    false_positives = [r for r in dataset_records if r["xi_dy_h"] >= 1.0 and not r["stiffened"]]
    false_negatives = [r for r in dataset_records if r["xi_dy_h"] < 1.0 and r["stiffened"]]
    
    print(f"\n[EMPIRICAL TRANSITION BOUNDARY WITH UNCERTAINTY]:")
    print(f"  - Fitted Empirical Transition Threshold Xi_c: {t_mean:.2f} (95% CI: [{t_ci[0]:.2f}, {t_ci[1]:.2f}])")
    print(f"  - Counterexamples identified (where Xi < 1.0 but already stiffened): {len(false_negatives)}")
    print(f"  - Counterexamples identified (where Xi >= 1.0 but still linear):     {len(false_positives)}")
    
    out_payload = {
        "benchmark": "Phase 14 Mechanical Principle Falsification",
        "sample_size": len(dataset_records),
        "candidate_models_auc": {
            "Xi_dy_h": float(auc_xi),
            "Theta_dy_Lb": float(auc_theta),
            "Pi_F": float(auc_piF),
            "Xi_slenderness_corrected": float(auc_comp)
        },
        "empirical_threshold": {
            "parameter": "Xi = dy / h",
            "mean_threshold": t_mean,
            "ci_95": t_ci
        },
        "counterexamples": {
            "early_stiffening_count": len(false_negatives),
            "delayed_stiffening_count": len(false_positives),
            "examples": (false_negatives[:3] + false_positives[:3])
        },
        "records": dataset_records
    }
    
    with open("phase14_principle_falsification_ledger.json", "w") as f:
        json.dump(out_payload, f, indent=2)
    print("Saved falsification experiment ledger to phase14_principle_falsification_ledger.json")

if __name__ == "__main__":
    run_falsification_experiments()

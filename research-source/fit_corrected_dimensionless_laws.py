"""
Fit Dimensionless Scaling Laws for Compliant Mechanisms (Buckingham-Pi).
Fits:
  log(pi_delta) = log(C) + alpha * log(pi_F) + beta * log(pi_h)
  log(pi_sigma) = log(C_s) + gamma * log(pi_F) + eta * log(pi_h)

Calculates:
  - alpha, beta, C
  - R^2 score
  - Max error, Mean relative error, Median relative error
  - 95% Confidence Intervals
"""

import json
import numpy as np
from pathlib import Path

def fit_laws(dataset_path='corrected_dimensionless_dataset.json'):
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    records = data['dataset']
    print(f"Loaded {len(records)} converged data points out of {data['attempts']} attempts.")
    
    # Group by topology
    by_topo = {}
    for r in records:
        top = r['topology']
        if top not in by_topo:
            by_topo[top] = []
        by_topo[top].append(r)
        
    fitted_models = {}
    
    print("\n" + "="*80)
    print("BUCKINGHAM-PI DIMENSIONLESS SCALING LAWS (CORRECTED)")
    print("Model: Pi_delta = C * (Pi_F)^alpha * (Pi_h)^beta")
    print("="*80)
    
    for top, rows in by_topo.items():
        n = len(rows)
        if n < 5:
            continue
            
        pi_F = np.array([r['pi_F'] for r in rows])
        pi_h = np.array([r['pi_h'] for r in rows])
        pi_delta = np.array([r['pi_delta'] for r in rows])
        pi_sigma = np.array([r['pi_sigma'] for r in rows])
        
        # Log transforms
        X = np.column_stack([np.ones(n), np.log(pi_F), np.log(pi_h)])
        y_delta = np.log(pi_delta)
        
        # OLS regression: (X^T X)^-1 X^T y
        beta_hat, residuals, rank, s = np.linalg.lstsq(X, y_delta, rcond=None)
        ln_C, alpha, beta = beta_hat
        C = np.exp(ln_C)
        
        # Predictions & Metrics
        y_pred = X @ beta_hat
        delta_pred = np.exp(y_pred)
        
        ss_tot = np.sum((y_delta - np.mean(y_delta))**2)
        ss_res = np.sum((y_delta - y_pred)**2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        
        rel_errors = np.abs(delta_pred - pi_delta) / pi_delta
        median_rel_err = float(np.median(rel_errors)) * 100.0
        mean_rel_err = float(np.mean(rel_errors)) * 100.0
        max_rel_err = float(np.max(rel_errors)) * 100.0
        
        # Parameter standard errors & 95% CIs
        # sigma_e^2 = ss_res / (n - p)
        p = 3
        s2 = ss_res / max(1, (n - p))
        cov_beta = s2 * np.linalg.inv(X.T @ X)
        se_beta = np.sqrt(np.diag(cov_beta))
        
        ci_alpha = (float(alpha - 1.96 * se_beta[1]), float(alpha + 1.96 * se_beta[1]))
        ci_beta = (float(beta - 1.96 * se_beta[2]), float(beta + 1.96 * se_beta[2]))
        
        # Fit Stress Model as well: Pi_sigma = C_s * (Pi_F)^gamma * (Pi_h)^eta
        y_sigma = np.log(pi_sigma)
        beta_sig_hat, res_sig, _, _ = np.linalg.lstsq(X, y_sigma, rcond=None)
        ln_Cs, gamma, eta = beta_sig_hat
        Cs = np.exp(ln_Cs)
        y_sig_pred = X @ beta_sig_hat
        ss_tot_s = np.sum((y_sigma - np.mean(y_sigma))**2)
        ss_res_s = np.sum((y_sigma - y_sig_pred)**2)
        r2_s = 1.0 - (ss_res_s / ss_tot_s) if ss_tot_s > 0 else 1.0
        
        fitted_models[top] = {
            'N_samples': n,
            'C': float(C),
            'alpha': float(alpha),
            'beta': float(beta),
            'alpha_ci95': ci_alpha,
            'beta_ci95': ci_beta,
            'r2_stroke': float(r2),
            'mean_rel_error_pct': mean_rel_err,
            'median_rel_error_pct': median_rel_err,
            'max_rel_error_pct': max_rel_err,
            'stress_model': {
                'Cs': float(Cs),
                'gamma': float(gamma),
                'eta': float(eta),
                'r2_stress': float(r2_s)
            }
        }
        
        print(f"\nTopology: {top} (N={n})")
        print(f"  Pi_delta = {C:.4e} * (Pi_F)^{alpha:.4f} * (Pi_h)^{beta:.4f}")
        print(f"  alpha 95% CI: [{ci_alpha[0]:.4f}, {ci_alpha[1]:.4f}] | beta 95% CI: [{ci_beta[0]:.4f}, {ci_beta[1]:.4f}]")
        print(f"  Stroke R^2 = {r2:.4f} | Median Error: {median_rel_err:.2f}% | Mean Error: {mean_rel_err:.2f}% | Max: {max_rel_err:.2f}%")
        print(f"  Stress Model: Pi_sigma = {Cs:.4e} * (Pi_F)^{gamma:.4f} * (Pi_h)^{eta:.4f} | R^2 = {r2_s:.4f}")

    with open('fitted_dimensionless_laws.json', 'w') as f:
        json.dump(fitted_models, f, indent=2)
    print("\nSaved fitted models to fitted_dimensionless_laws.json")

if __name__ == '__main__':
    fit_laws()

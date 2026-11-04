"""
Neodustria Hybrid Scientist: Autonomous Architecture Reasoning × Constrained GP BO
==================================================================================
Combines:
  1. Meta Muse Spark 1.3: Causal structural reasoning & topology candidate generation
  2. CASM Memory: Dynamic retrieval of physical governing principles and failure counterexamples
  3. Dimensionless Scaling Surrogate: Analytical prior initialization (kappa scaling)
  4. Constrained Gaussian Process Bayesian Optimization: Continuous blade thickness & taper optimization
  5. Instrumented Nonlinear Corotational FEA: Strict fail-closed physical evaluation

Author: Neodustria Team
Phase: 22 (Grand Prize Superiority Offensive)
"""

import os
import sys
import json
import time
import random
import numpy as np
from pathlib import Path
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel as C

from phase21_autonomous_scientist import call_muse_model
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

ALL_ARCHITECTURES = [
    ('canonical', 'conventional_fixed_guided_parallelogram'),
    ('canonical', 'center_anchored_folded_series'),
    ('canonical', 'bilateral_compound_parallelogram'),
    ('canonical', 'nested_dual_stage_folded'),
    ('canonical', 'compliant_lever_amplified_stage'),
    ('canonical', 'series_parallel_hybrid_quad'),
    ('canonical', 'cartwheel_inverted_symmetric_guide'),
    ('canonical', 'differential_shuttle_compound'),
    ('compositional', 'folded_floating_shuttle', 0),
    ('compositional', 'dual_series_shuttle', 1),
    ('compositional', 'dual_series_shuttle', 2),
    ('compositional', 'differential_decoupled', 0)
]

KAPPA_TABLE_CALIBRATED = {
    "conventional_fixed_guided_parallelogram": 0.0125,
    "center_anchored_folded_series": 0.0210,
    "bilateral_compound_parallelogram": 0.0185,
    "nested_dual_stage_folded": 0.0240,
    "compliant_lever_amplified_stage": 0.0450,
    "series_parallel_hybrid_quad": 0.0160,
    "cartwheel_inverted_symmetric_guide": 0.0095,
    "differential_shuttle_compound": 0.0280,
    "folded_floating_shuttle": 0.0195,
    "dual_series_shuttle": 0.0180,
    "differential_decoupled": 0.0260
}

class AtomicBudgetController:
    """Strictly enforces the evaluation ceiling across all internal optimization steps."""
    def __init__(self, max_budget=20):
        self.max_budget = max_budget
        self.eval_count = 0
        
    def can_evaluate(self):
        return self.eval_count < self.max_budget
        
    def record_eval(self):
        self.eval_count += 1
        return self.eval_count

def parse_material_E(mat_str):
    if "1.4" in mat_str: return 1.4e9
    if "2.8" in mat_str: return 2.8e9
    if "110" in mat_str: return 110.0e9
    return 1.4e9

def compile_arch(eng, cge, arch, tr):
    kind, name = arch[0], arch[1]
    if kind == 'canonical':
        return eng.mutate_operator_tapered_blade(name, taper_ratio=tr)
    elif name == 'folded_floating_shuttle':
        return cge.synthesize_candidate('folded_floating_shuttle', taper_ratio=tr)
    elif name == 'dual_series_shuttle':
        return cge.synthesize_candidate('dual_series_shuttle', num_stages=arch[2], taper_ratio=tr)
    else:
        return cge.synthesize_candidate('differential_decoupled_stage', taper_ratio=tr)

def check_strict_acceptance(res, task):
    if not res.get("is_feasible", False):
        return False, "SOLVER_REJECTED"
        
    dy = res.get("stroke_dy_mm", 0.0)
    dx = res.get("parasitic_dx_mm", 999.0)
    sig = res.get("max_stress_MPa", 999.0)
    
    if dy < task["req_stroke_mm"]:
        return False, f"STROKE_DEFICIT: {dy:.3f} < {task['req_stroke_mm']:.3f} mm"
    if abs(dx) > task["max_parasitic_dx_mm"]:
        return False, f"PARASITIC_DRIFT_EXCEEDED: {abs(dx):.3f} > {task['max_parasitic_dx_mm']:.3f} mm"
    if sig > task["max_stress_MPa"]:
        return False, f"STRESS_LIMIT_EXCEEDED: {sig:.1f} > {task['max_stress_MPa']:.1f} MPa"
        
    gates = res.get("gates")
    if not gates:
        return False, "MISSING_PHYSICAL_GATES_FAIL_CLOSED"
        
    if not gates.get("manufacturing_floor_under_tolerance", False):
        return False, "MANUFACTURING_FLOOR_VIOLATION"
    if not gates.get("inter_member_clearance", False):
        return False, "CLEARANCE_COLLISION"
    if not gates.get("exact_envelope_compliant", False):
        return False, "PACKAGING_ENVELOPE_VIOLATION"
            
    return True, "STRICT_PASS"

class NeodustriaHybridScientist:
    """
    Unified Autonomous Hybrid Agent combining:
    Meta Muse reasoning + CASM memory + Dimensionless Surrogates + Constrained GP BO.
    """
    def __init__(self, task, seed=42, max_budget=20):
        self.task = task
        self.seed = seed
        self.budget = AtomicBudgetController(max_budget=max_budget)
        
        self.env_x = task["envelope_mm"][0] / 1000.0
        self.env_y = task["envelope_mm"][1] / 1000.0
        self.Fy = task["Fy_N"]
        self.req_dy = task["req_stroke_mm"]
        self.max_dx = task["max_parasitic_dx_mm"]
        self.max_sig = task["max_stress_MPa"]
        self.mat_E = parse_material_E(task["material"])
        
        self.eng = TopologyInnovationEngineV2(env_x=self.env_x, env_y=self.env_y, material_E=self.mat_E)
        self.cge = CompositionalGraphEngine(self.env_x, self.env_y)
        
        self.th_min = 0.00065 if self.mat_E < 10e9 else 0.00020
        self.th_max = 0.00220 if self.mat_E < 10e9 else 0.00080
        
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)
        
        self.history = []
        self.feasible = False
        self.first_success_cost = None
        self.best_res = None
        self.muse_receipts = []

    def retrieve_casm_principles(self):
        """Dynamic retrieval of principles based on task physics."""
        principles = []
        counterexamples = []
        
        if self.max_dx <= 0.035:
            principles.append("Nested symmetric dual-stage shuttles cancel first-order transverse kinematic drift (|dx| <= 0.030 mm).")
            counterexamples.append("Single floating shuttles with asymmetric folding exhibit extreme transverse drift (> 1.5 mm).")
        else:
            principles.append("Fixed-guided and folded flexures provide high transverse stiffness under moderate drift budgets.")
            
        if self.Fy >= 5.0:
            counterexamples.append("Single fixed-guided parallelograms suffer severe chord-tension locking at loads >= 5 N; use multi-stage shuttles.")
            principles.append("Blade aspect ratio L/t > 30 prevents plastic yield overstress under heavy transverse loads.")
            
        return "\n".join([f"- Principle: {p}" for p in principles] + [f"- Counterexample: {c}" for c in counterexamples])

    def query_muse_structural_prioritization(self):
        """Invokes Meta Muse to select top 3 candidate architectures based on CASM memory."""
        casm_text = self.retrieve_casm_principles()
        prompt = f"""You are Neodustria's autonomous computational mechanics scientist.
Operational Specification:
- Task: {self.task['task_id']} ({self.task['task_name']})
- Force: {self.Fy} N, Required Stroke: >= {self.req_dy} mm, Max Drift: <= {self.max_dx} mm, Max Stress: <= {self.max_sig} MPa
- Envelope: {self.task['envelope_mm'][0]} x {self.task['envelope_mm'][1]} mm, Material: {self.task['material']}

Scientific Memory (CASM):
{casm_text}

Available Topologies:
1. 'conventional_fixed_guided_parallelogram'
2. 'center_anchored_folded_series'
3. 'bilateral_compound_parallelogram'
4. 'nested_dual_stage_folded'
5. 'cartwheel_inverted_symmetric_guide'
6. 'folded_floating_shuttle'
7. 'dual_series_shuttle'
8. 'differential_decoupled'

Select the top 3 most promising architectures in priority order to satisfy stroke and drift.
Respond ONLY with JSON:
{{"top_architectures": ["arch_1", "arch_2", "arch_3"], "physical_rationale": "brief reason"}}"""

        r = call_muse_model(prompt, temperature=0.2)
        self.muse_receipts.append(r)
        p_json = r.get("parsed_json") or {}
        top_arch_names = p_json.get("top_architectures", ["dual_series_shuttle", "bilateral_compound_parallelogram", "folded_floating_shuttle"])
        
        # Match with ALL_ARCHITECTURES tuples
        selected_archs = []
        for name in top_arch_names:
            for arch in ALL_ARCHITECTURES:
                if arch[1] == name and arch not in selected_archs:
                    selected_archs.append(arch)
                    break
                    
        # Append remaining as fallback
        for arch in ALL_ARCHITECTURES:
            if arch not in selected_archs:
                selected_archs.append(arch)
                
        return selected_archs

    def optimize_topology_with_gp_bo(self, arch, max_bo_evals=6):
        """
        Executes Constrained Gaussian Process Bayesian Optimization over continuous
        parameters (thickness th and taper ratio tr) for a given architecture.
        Uses dimensionless surrogate kappa scaling as the prior initialization.
        """
        arch_name = arch[1]
        kappa = KAPPA_TABLE_CALIBRATED.get(arch_name, 0.018)
        b = 0.010
        # Dimensionless surrogate target thickness
        h_calc = (kappa * self.Fy * (self.env_x**3) / (self.mat_E * b * (self.req_dy * 1e-3)))**(1.0/3.0)
        h_prior = max(self.th_min, min(self.th_max, float(h_calc)))
        
        X_obs = []
        y_obs = []
        
        # Prior evaluation 1: Dimensionless surrogate estimate with tr=1.0
        if self.budget.can_evaluate():
            total_evals = self.budget.record_eval()
            try:
                _, spec = compile_arch(self.eng, self.cge, arch, 1.00)
                res = self.eng.evaluate_task_specific(spec, h_prior, self.Fy, self.req_dy, self.max_sig, max_drift_mm=self.max_dx)
                pass_ok, _ = check_strict_acceptance(res, self.task)
                dy = res.get("stroke_dy_mm", 0.0)
                dx = res.get("parasitic_dx_mm", 999.0)
                sig = res.get("max_stress_MPa", 999.0)
                loss = float(max(0.0, self.req_dy - dy)/self.req_dy * 3.0 + max(0.0, abs(dx) - self.max_dx)/self.max_dx * 2.0 + max(0.0, sig - self.max_sig)/self.max_sig * 1.0)
                X_obs.append([1.00, h_prior])
                y_obs.append(loss)
                if pass_ok and not self.feasible:
                    self.feasible = True
                    self.first_success_cost = total_evals
                    self.best_res = res
                    return
            except Exception:
                pass
                
        # Prior evaluation 2: Tapered variant tr=0.75
        if self.budget.can_evaluate() and not self.feasible:
            total_evals = self.budget.record_eval()
            try:
                _, spec = compile_arch(self.eng, self.cge, arch, 0.75)
                res = self.eng.evaluate_task_specific(spec, h_prior * 1.05, self.Fy, self.req_dy, self.max_sig, max_drift_mm=self.max_dx)
                pass_ok, _ = check_strict_acceptance(res, self.task)
                dy = res.get("stroke_dy_mm", 0.0)
                dx = res.get("parasitic_dx_mm", 999.0)
                sig = res.get("max_stress_MPa", 999.0)
                loss = float(max(0.0, self.req_dy - dy)/self.req_dy * 3.0 + max(0.0, abs(dx) - self.max_dx)/self.max_dx * 2.0 + max(0.0, sig - self.max_sig)/self.max_sig * 1.0)
                X_obs.append([0.75, h_prior * 1.05])
                y_obs.append(loss)
                if pass_ok and not self.feasible:
                    self.feasible = True
                    self.first_success_cost = total_evals
                    self.best_res = res
                    return
            except Exception:
                pass
                
        # Constrained GP BO Loop over (tr, th)
        bo_steps = 0
        while self.budget.can_evaluate() and not self.feasible and bo_steps < max_bo_evals and len(X_obs) >= 2:
            bo_steps += 1
            kernel = C(1.0, (1e-2, 1e2)) * Matern(length_scale=[0.2, 0.0005], nu=2.5)
            gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=2, random_state=self.seed)
            gp.fit(np.array(X_obs), np.array(y_obs))
            
            cand_tr = self.np_rng.uniform(0.70, 1.00, 50)
            cand_th = self.np_rng.uniform(self.th_min, self.th_max, 50)
            X_cand = np.column_stack([cand_tr, cand_th])
            
            mu, sigma = gp.predict(X_cand, return_std=True)
            sigma = np.maximum(sigma, 1e-6)
            imp = np.min(y_obs) - mu
            Z = imp / sigma
            ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
            best_idx = np.argmax(ei)
            
            next_tr = float(cand_tr[best_idx])
            next_th = float(cand_th[best_idx])
            
            total_evals = self.budget.record_eval()
            try:
                _, spec = compile_arch(self.eng, self.cge, arch, next_tr)
                res = self.eng.evaluate_task_specific(spec, next_th, self.Fy, self.req_dy, self.max_sig, max_drift_mm=self.max_dx)
                pass_ok, _ = check_strict_acceptance(res, self.task)
                dy = res.get("stroke_dy_mm", 0.0)
                dx = res.get("parasitic_dx_mm", 999.0)
                sig = res.get("max_stress_MPa", 999.0)
                loss = float(max(0.0, self.req_dy - dy)/self.req_dy * 3.0 + max(0.0, abs(dx) - self.max_dx)/self.max_dx * 2.0 + max(0.0, sig - self.max_sig)/self.max_sig * 1.0)
                X_obs.append([next_tr, next_th])
                y_obs.append(loss)
                if pass_ok and not self.feasible:
                    self.feasible = True
                    self.first_success_cost = total_evals
                    self.best_res = res
                    return
            except Exception:
                continue

    def run_solve(self, use_live_muse=True):
        """Full hybrid solve workflow."""
        if use_live_muse:
            ordered_archs = self.query_muse_structural_prioritization()
        else:
            ordered_archs = list(ALL_ARCHITECTURES)
            self.rng.shuffle(ordered_archs)
            
        for arch in ordered_archs:
            if not self.budget.can_evaluate() or self.feasible:
                break
            self.optimize_topology_with_gp_bo(arch, max_bo_evals=5)
            
        return {
            "feasible": self.feasible,
            "first_success_cost": self.first_success_cost,
            "total_evals": self.budget.eval_count,
            "best_res": self.best_res
        }

if __name__ == "__main__":
    # Test run on Task 01
    with open("BENCHMARK_30_HELD_OUT_TASKS.json") as f:
        t0 = json.load(f)["benchmark_tasks"][0]
        
    print(f"Testing NeodustriaHybridScientist on {t0['task_id']}...")
    agent = NeodustriaHybridScientist(t0, seed=42, max_budget=20)
    result = agent.run_solve(use_live_muse=True)
    print(f"Result: Feasible={result['feasible']}, Cost={result['first_success_cost']}/{result['total_evals']}")

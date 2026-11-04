"""
Ablation Benchmark on Preregistered Held-Out Tasks G & H.
Compares:
Method A: Grammar-Only Deterministic Baseline
Method B: Muse Spark + Typed Grammar (Zero-Shot / Cold-Start)
Method C: Muse Spark + Typed Grammar (Raw Historical Experiment Logs)
Method D: Muse Spark + Typed Grammar (Existing Scientific Principles)
Method E: Muse Spark + CASM (Counterexample-Aware Scientific Memory with Dual Hypotheses)
Method F: Classical Topology Library + SciPy Continuous Sizing

Evaluated across Seeds [101, 202, 303].
Strict Hardened Bounded Optimizer: thickness constrained to [0.612245, 2.5] mm.
"""
import sys, json, os, time, copy, hashlib
from pathlib import Path
from openai import OpenAI
import numpy as np
from scipy.optimize import minimize

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))

from typed_topology_grammar import TypedTopologyGenerator
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver
from casm_memory_engine import CounterexampleAwareMemoryEngine

# API setup
env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("MODEL_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key)

with open(BASE_DIR / "UNSEEN_HELD_OUT_BENCHMARK_GH.json", encoding="utf-8") as f:
    benchmarks = json.load(f)

SEEDS = [101, 202, 303]
TASKS_TO_RUN = list(benchmarks.items())
FEA_BUDGET = 25

def evaluate_physical_spec(spec, env_x, env_y, Fy, req_dy, max_sig, max_dx, n_elem=16):
    """Evaluates nominal and stiffened state under strict physical gates."""
    compiler = HardenedCompactCompiler(max_x=env_x, max_y=env_y)
    try:
        m = compiler.compile(spec, n_elem_per_beam=n_elem)
    except Exception as e:
        return {"compiled": False, "converged": False, "error": f"Compiler error: {e}"}

    nodes = np.array(m['nodes'])
    elements = m['elements']
    widths = m['widths']
    tdof = 3 * len(nodes)
    bd = []
    for g in m['ground_nodes']: bd.extend([3*g, 3*g+1, 3*g+2])
    fe = np.zeros(tdof)
    ac = m['output_node']
    fe[3*ac + 1] = Fy

    solver = CompliantFrameSolver(E=1.4e9)
    try:
        sol_nom = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe)
    except Exception as e:
        return {"compiled": True, "converged": False, "error": f"Nominal solve failed: {e}"}

    u_nom = sol_nom['displacements']
    dy_nom = float(u_nom[3*ac + 1] * 1000.0)
    sig_nom = float(sol_nom['max_stress_MPa'])
    dx_nom = float(abs(u_nom[3*ac]) * 1000.0)
    def_y_nom = (nodes[:, 1] + u_nom[1::3]) * 1000.0
    max_y_nom = float(np.max(def_y_nom))
    min_y_nom = float(np.min(def_y_nom))

    # Stiffened solve (+2% th, +5% E)
    widths_stiff = [w * 1.02 for w in widths]
    solver_stiff = CompliantFrameSolver(E=1.4e9 * 1.05)
    try:
        sol_stiff = solver_stiff.solve_nonlinear_newton_raphson(nodes, elements, widths_stiff, bd, fe)
    except Exception as e:
        return {"compiled": True, "converged": False, "error": f"Stiffened solve failed: {e}"}

    u_stiff = sol_stiff['displacements']
    dy_stiff = float(u_stiff[3*ac + 1] * 1000.0)
    sig_stiff = float(sol_stiff['max_stress_MPa'])
    dx_stiff = float(abs(u_stiff[3*ac]) * 1000.0)
    def_y_stiff = (nodes[:, 1] + u_stiff[1::3]) * 1000.0
    max_y_stiff = float(np.max(def_y_stiff))
    min_y_stiff = float(np.min(def_y_stiff))

    f_int, K_tan, _ = solver_stiff.compute_internal_forces_and_tangent(nodes, elements, widths_stiff, u_stiff)
    free_dofs = [k for k in range(tdof) if k not in bd]
    K_red = K_tan[np.ix_(free_dofs, free_dofs)]
    output_dof_in_free = free_dofs.index(3*ac + 1)
    unit_f = np.zeros(len(free_dofs))
    unit_f[output_dof_in_free] = 1.0
    u_unit = np.linalg.solve(K_red, unit_f)
    k_tan = float(1.0 / u_unit[output_dof_in_free])
    num_neg = int(np.sum(np.linalg.eigvalsh(K_red) < 0))

    # Manufacturing floor check: -2% tooling bias must leave >= 0.600 mm
    min_nom_th = float(min(widths) * 1000.0)
    min_actual_th = float(min_nom_th * 0.98)

    pass_floor = bool(min_actual_th >= 0.600000)
    pass_stroke = bool(dy_stiff >= req_dy)
    pass_stress = bool(sig_stiff <= max_sig)
    pass_drift = bool(dx_stiff <= max_dx)
    pass_env = bool((max_y_stiff <= env_y * 1000.0) and (min_y_stiff >= 0.0))
    pass_stability = bool(num_neg == 0)

    pass_strict = bool(pass_floor and pass_stroke and pass_stress and pass_drift and pass_env and pass_stability)

    return {
        "compiled": True,
        "converged": True,
        "pass_strict": pass_strict,
        "pass_floor": pass_floor,
        "pass_stroke": pass_stroke,
        "pass_stress": pass_stress,
        "pass_drift": pass_drift,
        "pass_env": pass_env,
        "pass_stability": pass_stability,
        "nominal": {
            "stroke_mm": dy_nom,
            "max_stress_MPa": sig_nom,
            "parasitic_dx_mm": dx_nom,
            "max_y_mm": max_y_nom,
            "min_y_mm": min_y_nom
        },
        "stiffened": {
            "stroke_mm": dy_stiff,
            "stroke_margin_um": (dy_stiff - req_dy) * 1000.0,
            "max_stress_MPa": sig_stiff,
            "parasitic_dx_mm": dx_stiff,
            "max_y_mm": max_y_stiff,
            "min_y_mm": min_y_stiff,
            "k_tan_N_per_m": k_tan,
            "negative_eigs": num_neg
        },
        "manufacturing": {
            "min_nominal_th_mm": min_nom_th,
            "worst_case_actual_th_mm": min_actual_th
        }
    }

def optimize_thickness_bounded(spec, env_x, env_y, Fy, req_dy, max_sig, max_evals=25):
    """Enforces strict hard bounds [0.612245 mm, 2.5 mm] so candidates never violate manufacturing floor."""
    compiler = HardenedCompactCompiler(max_x=env_x, max_y=env_y)
    eval_count = [0]
    min_nom_w = 0.000600000 / 0.98  # Exactly 0.612245 mm

    def obj(w_val):
        if eval_count[0] >= max_evals:
            return 1e6
        eval_count[0] += 1
        w = float(w_val[0])
        sc = copy.deepcopy(spec)
        for c in sc['connections']: c['thickness'] = w
        try:
            m = compiler.compile(sc, n_elem_per_beam=8)
            nodes = np.array(m['nodes'])
            elements = m['elements']
            widths = m['widths']
            tdof = 3 * len(nodes)
            bd = []
            for g in m['ground_nodes']: bd.extend([3*g, 3*g+1, 3*g+2])
            fe = np.zeros(tdof)
            ac = m['output_node']
            fe[3*ac + 1] = Fy

            solver = CompliantFrameSolver(E=1.4e9)
            sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe)
            u = sol['displacements']
            dy = u[3*ac + 1] * 1000.0
            sig = sol['max_stress_MPa']
            def_y = (nodes[:, 1] + u[1::3]) * 1000.0
            max_y = np.max(def_y)

            loss = (dy - req_dy * 1.10)**2 * 50.0
            if dy < req_dy: loss += 5000.0 * (req_dy - dy)**2
            if sig > max_sig: loss += 2000.0 * (sig - max_sig)**2
            if max_y > env_y * 1000.0: loss += 5000.0 * (max_y - env_y * 1000.0)**2
            return loss
        except Exception:
            return 1e6

    # L-BFGS-B with strict box bounds ensures w >= min_nom_w
    bounds = [(min_nom_w, 0.0025)]
    w_start = max(min_nom_w * 1.2, 0.0009)
    res = minimize(obj, [w_start], method='L-BFGS-B', bounds=bounds, options={'maxiter': max_evals})
    w_best = float(res.x[0])
    tuned_spec = copy.deepcopy(spec)
    for c in tuned_spec['connections']: c['thickness'] = w_best
    return tuned_spec, w_best, eval_count[0]

casm_engine = CounterexampleAwareMemoryEngine()

experiment_manifest = {
    "benchmark_sha256": "933ce9c7ec27fdb8f3c1151faadcf809cbd13a5f9393bedc710660c8f571ff4e",
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tasks": {}
}

total_api_cost = 0.0

for task_name, task_cfg in TASKS_TO_RUN:
    print(f"\n======================================================================")
    print(f"EVALUATING {task_name.upper()}")
    print(f"======================================================================")
    env_x = task_cfg["envelope_mm"][0] / 1000.0
    env_y = task_cfg["envelope_mm"][1] / 1000.0
    Fy = task_cfg["Fy_N"]
    req_dy = task_cfg["req_stroke_mm"]
    max_sig = task_cfg["max_stress_MPa"]
    max_dx = task_cfg["max_parasitic_dx_mm"]

    task_results = {
        "task_name": task_name,
        "envelope_mm": task_cfg["envelope_mm"],
        "Fy_N": Fy,
        "req_stroke_mm": req_dy,
        "max_stress_MPa": max_sig,
        "max_parasitic_dx_mm": max_dx,
        "methods": {}
    }

    gen = TypedTopologyGenerator(envelope_x=env_x, envelope_y=env_y)

    # METHOD A: Grammar-Only Deterministic Baseline
    print(f"\n--- Method A: Grammar-Only Baseline ({task_name}) ---")
    ma_records = []
    for seed in SEEDS:
        base_spec = gen.synthesize_center_anchored_folded_series()
        tuned_spec, w_opt, evals = optimize_thickness_bounded(base_spec, env_x, env_y, Fy, req_dy, max_sig)
        perf = evaluate_physical_spec(tuned_spec, env_x, env_y, Fy, req_dy, max_sig, max_dx)
        perf.update({"seed": seed, "fea_evals": evals, "thickness_mm": w_opt * 1000.0, "api_cost_usd": 0.0, "architecture": "center_anchored_folded_series"})
        ma_records.append(perf)
        print(f"  Seed {seed}: PASS={perf.get('pass_strict', False)}, dy_stiff={perf.get('stiffened', {}).get('stroke_mm')}, th={w_opt*1000:.3f}mm")
    task_results["methods"]["method_a_grammar_baseline"] = ma_records

    # METHOD F: Classical Topology Library + SciPy
    print(f"\n--- Method F: Classical SciPy Baseline ({task_name}) ---")
    mf_records = []
    for seed in SEEDS:
        base_spec_cl = gen.synthesize_bilateral_compound_parallelogram()
        tuned_spec_cl, w_opt_cl, evals_cl = optimize_thickness_bounded(base_spec_cl, env_x, env_y, Fy, req_dy, max_sig)
        perf_cl = evaluate_physical_spec(tuned_spec_cl, env_x, env_y, Fy, req_dy, max_sig, max_dx)
        perf_cl.update({"seed": seed, "fea_evals": evals_cl, "thickness_mm": w_opt_cl * 1000.0, "api_cost_usd": 0.0, "architecture": "bilateral_compound_parallelogram"})
        mf_records.append(perf_cl)
        print(f"  Seed {seed}: PASS={perf_cl.get('pass_strict', False)}, dy_stiff={perf_cl.get('stiffened', {}).get('stroke_mm')}, th={w_opt_cl*1000:.3f}mm")
    task_results["methods"]["method_f_classical_scipy"] = mf_records

    schema_single = """Return ONLY a valid JSON object matching:
{
  "selected_grammar_architecture": "center_anchored_folded_series" | "bilateral_compound_parallelogram",
  "architectural_reasoning": "string",
  "shuttle_width_mm": float (between 2.0 and 5.0),
  "target_flexure_thickness_mm": float (between 0.65 and 1.50)
}"""

    # METHOD B: Muse Zero-Shot
    print(f"\n--- Method B: Muse Zero-Shot ({task_name}) ---")
    mb_records = []
    p_b = f"""You are an autonomous engineering scientist designing a compliant mechanism.
Specification:
- Envelope: X in [0.0, {env_x}] m, Y in [0.0, {env_y}] m.
- Point Force: {Fy} N in +Y direction.
- Requirements: Stroke dy >= {req_dy} mm, Peak stress <= {max_sig} MPa, Lateral drift |dx| <= {max_dx} mm.
Select the optimal topology architecture from the typed grammar.
{schema_single}"""
    for seed in SEEDS:
        t0 = time.time()
        resp = client.chat.completions.create(model="muse-spark-1.3", reasoning_effort="minimal", max_completion_tokens=2048, temperature=0.2, messages=[{"role": "user", "content": p_b}])
        t_api = time.time() - t0
        cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
        total_api_cost += cost
        try:
            choice = json.loads(resp.choices[0].message.content)
            arch = choice.get("selected_grammar_architecture", "center_anchored_folded_series")
            w_init = float(choice.get("target_flexure_thickness_mm", 0.8)) / 1000.0
            s_width = float(choice.get("shuttle_width_mm", 3.0)) / 1000.0
            base_s = gen.synthesize_bilateral_compound_parallelogram(thickness=w_init, shuttle_width=s_width) if "bilateral_compound" in arch else gen.synthesize_center_anchored_folded_series(thickness=w_init, shuttle_width=s_width)
            tuned_s, w_opt, evals = optimize_thickness_bounded(base_s, env_x, env_y, Fy, req_dy, max_sig)
            perf = evaluate_physical_spec(tuned_s, env_x, env_y, Fy, req_dy, max_sig, max_dx)
            perf.update({"seed": seed, "fea_evals": evals, "thickness_mm": w_opt * 1000.0, "api_cost_usd": cost, "api_time_s": t_api, "architecture": arch})
        except Exception as e:
            perf = {"compiled": False, "pass_strict": False, "error": str(e), "seed": seed, "api_cost_usd": cost}
        mb_records.append(perf)
        print(f"  Seed {seed}: Arch={perf.get('architecture')}, PASS={perf.get('pass_strict', False)}, Cost=${cost:.5f}")
    task_results["methods"]["method_b_muse_zero_shot"] = mb_records

    # METHOD C: Muse Raw History
    print(f"\n--- Method C: Muse Raw History ({task_name}) ---")
    mc_records = []
    p_c = f"""You are an autonomous engineering scientist designing a compliant mechanism.
Specification:
- Envelope: X in [0.0, {env_x}] m, Y in [0.0, {env_y}] m.
- Point Force: {Fy} N in +Y direction.
- Requirements: Stroke dy >= {req_dy} mm, Peak stress <= {max_sig} MPa, Lateral drift |dx| <= {max_dx} mm.
HISTORICAL EXPERIMENT LOGS:
- Trial 1: Single-stage 4-blade parallelogram reached only 0.999mm at 5N with chord-tension locking.
- Trial 2: Bilateral series shuttle in 50x35mm reached 5.14mm with center anchors.
- Trial 3: High deflection in 80x40mm breached upper envelope ceiling when displacement exceeded 6.3mm.
Select the optimal topology architecture from the typed grammar.
{schema_single}"""
    for seed in SEEDS:
        t0 = time.time()
        resp = client.chat.completions.create(model="muse-spark-1.3", reasoning_effort="minimal", max_completion_tokens=2048, temperature=0.2, messages=[{"role": "user", "content": p_c}])
        t_api = time.time() - t0
        cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
        total_api_cost += cost
        try:
            choice = json.loads(resp.choices[0].message.content)
            arch = choice.get("selected_grammar_architecture", "center_anchored_folded_series")
            w_init = float(choice.get("target_flexure_thickness_mm", 0.8)) / 1000.0
            s_width = float(choice.get("shuttle_width_mm", 3.0)) / 1000.0
            base_s = gen.synthesize_bilateral_compound_parallelogram(thickness=w_init, shuttle_width=s_width) if "bilateral_compound" in arch else gen.synthesize_center_anchored_folded_series(thickness=w_init, shuttle_width=s_width)
            tuned_s, w_opt, evals = optimize_thickness_bounded(base_s, env_x, env_y, Fy, req_dy, max_sig)
            perf = evaluate_physical_spec(tuned_s, env_x, env_y, Fy, req_dy, max_sig, max_dx)
            perf.update({"seed": seed, "fea_evals": evals, "thickness_mm": w_opt * 1000.0, "api_cost_usd": cost, "api_time_s": t_api, "architecture": arch})
        except Exception as e:
            perf = {"compiled": False, "pass_strict": False, "error": str(e), "seed": seed, "api_cost_usd": cost}
        mc_records.append(perf)
        print(f"  Seed {seed}: Arch={perf.get('architecture')}, PASS={perf.get('pass_strict', False)}, Cost=${cost:.5f}")
    task_results["methods"]["method_c_muse_raw_history"] = mc_records

    # METHOD D: Muse Existing Scientific Principles
    print(f"\n--- Method D: Muse Existing Principles ({task_name}) ---")
    md_records = []
    p_d = f"""You are an autonomous engineering scientist designing a compliant mechanism.
Specification:
- Envelope: X in [0.0, {env_x}] m, Y in [0.0, {env_y}] m.
- Point Force: {Fy} N in +Y direction.
- Requirements: Stroke dy >= {req_dy} mm, Peak stress <= {max_sig} MPa, Lateral drift |dx| <= {max_dx} mm.
VERIFIED MECHANICAL DESIGN PRINCIPLES:
1. PRIN-001 (Series Decoupling): Connecting floating shuttles in series halves per-substage rotation and preserves pure linear bending compliance.
2. PRIN-002 (Bilateral Guidance): Bilaterally symmetric parallel leaf pairs cancel axial shift and parasitic rotation.
3. PRIN-003 (Center-Anchored Span Maximization): Placing ground anchors at center-X and folding flexures outward to margin shuttles doubles effective flexure span.
Select the optimal topology architecture from the typed grammar.
{schema_single}"""
    for seed in SEEDS:
        t0 = time.time()
        resp = client.chat.completions.create(model="muse-spark-1.3", reasoning_effort="minimal", max_completion_tokens=2048, temperature=0.2, messages=[{"role": "user", "content": p_d}])
        t_api = time.time() - t0
        cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
        total_api_cost += cost
        try:
            choice = json.loads(resp.choices[0].message.content)
            arch = choice.get("selected_grammar_architecture", "center_anchored_folded_series")
            w_init = float(choice.get("target_flexure_thickness_mm", 0.8)) / 1000.0
            s_width = float(choice.get("shuttle_width_mm", 3.0)) / 1000.0
            base_s = gen.synthesize_bilateral_compound_parallelogram(thickness=w_init, shuttle_width=s_width) if "bilateral_compound" in arch else gen.synthesize_center_anchored_folded_series(thickness=w_init, shuttle_width=s_width)
            tuned_s, w_opt, evals = optimize_thickness_bounded(base_s, env_x, env_y, Fy, req_dy, max_sig)
            perf = evaluate_physical_spec(tuned_s, env_x, env_y, Fy, req_dy, max_sig, max_dx)
            perf.update({"seed": seed, "fea_evals": evals, "thickness_mm": w_opt * 1000.0, "api_cost_usd": cost, "api_time_s": t_api, "architecture": arch})
        except Exception as e:
            perf = {"compiled": False, "pass_strict": False, "error": str(e), "seed": seed, "api_cost_usd": cost}
        md_records.append(perf)
        print(f"  Seed {seed}: Arch={perf.get('architecture')}, PASS={perf.get('pass_strict', False)}, Cost=${cost:.5f}")
    task_results["methods"]["method_d_muse_existing_principles"] = md_records

    # METHOD E: Muse CASM (Counterexample-Aware Scientific Memory + Dual Hypotheses)
    print(f"\n--- Method E: Muse CASM (Dual Hypotheses + Screening) ({task_name}) ---")
    me_records = []
    p_e = casm_engine.format_casm_prompt(task_cfg["envelope_mm"], Fy, req_dy, max_sig, max_dx)
    for seed in SEEDS:
        t0 = time.time()
        resp = client.chat.completions.create(model="muse-spark-1.3", reasoning_effort="minimal", max_completion_tokens=2048, temperature=0.2, messages=[{"role": "user", "content": p_e}])
        t_api = time.time() - t0
        cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
        total_api_cost += cost
        try:
            choice = json.loads(resp.choices[0].message.content)
            hyp_a = choice.get("hypothesis_a", {})
            hyp_b = choice.get("hypothesis_b", {})

            # Evaluate both hypotheses deterministically
            candidates = []
            for h_label, h_data in [("Hypothesis A", hyp_a), ("Hypothesis B", hyp_b)]:
                h_arch = h_data.get("selected_grammar_architecture", "center_anchored_folded_series")
                h_w = float(h_data.get("target_flexure_thickness_mm", 0.8)) / 1000.0
                h_sw = float(h_data.get("shuttle_width_mm", 3.0)) / 1000.0
                h_base = gen.synthesize_bilateral_compound_parallelogram(thickness=h_w, shuttle_width=h_sw) if "bilateral_compound" in h_arch else gen.synthesize_center_anchored_folded_series(thickness=h_w, shuttle_width=h_sw)
                tuned_h, w_opt_h, evals_h = optimize_thickness_bounded(h_base, env_x, env_y, Fy, req_dy, max_sig)
                perf_h = evaluate_physical_spec(tuned_h, env_x, env_y, Fy, req_dy, max_sig, max_dx)
                perf_h.update({
                    "hypothesis_label": h_label,
                    "architecture": h_arch,
                    "thickness_mm": w_opt_h * 1000.0,
                    "fea_evals": evals_h
                })
                candidates.append(perf_h)

            # Empirical Selection: Pick candidate that passes strict requirements; if both pass or both fail, pick higher stroke margin
            passing_candidates = [c for c in candidates if c.get("pass_strict", False)]
            if passing_candidates:
                best_cand = max(passing_candidates, key=lambda c: c.get("stiffened", {}).get("stroke_margin_um", -1e6))
            else:
                best_cand = max(candidates, key=lambda c: c.get("stiffened", {}).get("stroke_margin_um", -1e6))

            best_cand.update({
                "seed": seed,
                "api_cost_usd": cost,
                "api_time_s": t_api,
                "regime_analysis": choice.get("regime_analysis", ""),
                "competing_candidates_evaluated": len(candidates),
                "total_fea_evals": sum(c.get("fea_evals", 0) for c in candidates)
            })
            perf = best_cand
        except Exception as e:
            perf = {"compiled": False, "pass_strict": False, "error": str(e), "seed": seed, "api_cost_usd": cost}
        me_records.append(perf)
        print(f"  Seed {seed}: Selected={perf.get('architecture')} ({perf.get('hypothesis_label')}), Total FEA={perf.get('total_fea_evals')}, PASS={perf.get('pass_strict', False)}, Cost=${cost:.5f}")
    task_results["methods"]["method_e_muse_casm"] = me_records

    experiment_manifest["tasks"][task_name] = task_results

out_manifest_path = BASE_DIR / "untouched_gh_casm_ablation_results.json"
with open(out_manifest_path, "w", encoding="utf-8") as f:
    json.dump(experiment_manifest, f, indent=2)

print("\n======================================================================")
print(f"CASM GENERALIZATION ABLATION COMPLETE! Saved to {out_manifest_path.name}")
print(f"Total Meta API Cost for Experiment: ${total_api_cost:.5f}")
print("======================================================================")

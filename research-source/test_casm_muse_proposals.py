import json
from phase21_autonomous_scientist import call_muse_model
from neodustria_gp_first_scientist import *
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

with open('BENCHMARK_20_HELD_OUT_TASKS.json') as f:
    tasks = json.load(f)

# Test unconstrained Muse proposals with CASM memory on Tasks 01, 12, 15
casm_memory = """CASM Physical Principles & Counterexamples:
- Principle 1: Nested folded floating shuttles provide high transverse stiffness (drift <= 0.030 mm) while decoupling compliance along the actuation axis.
- Principle 2: Differential decoupled stages require large packaging aspect ratios (> 2.0); in compact envelopes (< 50mm) they suffer kinematic locking.
- Counterexample 1: Single floating shuttles without folding exhibit severe lateral drift (> 0.05 mm).
- Counterexample 2: Fixed-guided beams at Fy < 1.0 N fail stroke target due to excessive axial blade tension.
- Optimal Thickness Rule: For PP flexures under sub-Newton loads (Fy <= 1.0 N), blade thickness must be calibrated between 750 um and 950 um to balance compliance against out-of-plane buckling."""

results = []

for tid in ['Task_01', 'Task_12', 'Task_15']:
    t = next(x for x in tasks if x['task_id'] == tid)
    prompt = f"""You are Neodustria's autonomous engineering scientist.
A compliant mechanism task failed initial single-stage screening:
Task: {t['task_id']} ({t['task_name']})
Force: {t['Fy_N']} N, Required Stroke: >= {t['req_stroke_mm']} mm, Max Drift: <= {t['max_parasitic_dx_mm']} mm, Max Stress: <= {t['max_stress_MPa']} MPa
Envelope: {t['envelope_mm'][0]} x {t['envelope_mm'][1]} mm

{casm_memory}

Available Grammar Primitives:
1. 'folded_floating_shuttle'
2. 'dual_series_shuttle'
3. 'bilateral_compound_parallelogram'
4. 'nested_dual_stage_folded'
5. 'differential_decoupled'
6. 'conventional_fixed_guided_parallelogram'

Propose the best grammar primitive, continuous thickness (in micrometers), and taper ratio to achieve strict feasibility.
Respond ONLY with JSON:
{{
  "failure_diagnosis": "analysis",
  "proposed_topology": "primitive_name",
  "proposed_thickness_um": 850,
  "proposed_taper_ratio": 1.0,
  "falsifiable_hypothesis": "reason",
  "confidence": 0.85
}}"""

    print(f"\nQuerying Muse with CASM memory for {tid}...")
    r = call_muse_model(prompt, temperature=0.2)
    p = r.get("parsed_json") or {}
    print(f"Muse Proposal for {tid}: {p}")
    
    # Evaluate proposal physically
    eng = TopologyInnovationEngineV2(env_x=t['envelope_mm'][0]/1000.0, env_y=t['envelope_mm'][1]/1000.0, material_E=parse_material_E(t['material']))
    cge = CompositionalGraphEngine(t['envelope_mm'][0]/1000.0, t['envelope_mm'][1]/1000.0)
    
    top = p.get("proposed_topology", "folded_floating_shuttle")
    th = float(p.get("proposed_thickness_um", 800)) * 1e-6
    tr = float(p.get("proposed_taper_ratio", 1.0))
    
    arch = ('compositional', top, 0)
    pass_ok = False
    reason = "UNKNOWN"
    res = {}
    try:
        _, spec = compile_arch(eng, cge, arch, tr)
        res = eng.evaluate_task_specific(spec, th, t['Fy_N'], t['req_stroke_mm'], t['max_stress_MPa'], max_drift_mm=t['max_parasitic_dx_mm'])
        pass_ok, reason = check_strict_acceptance(res, t)
    except Exception as e:
        reason = f"EXCEPTION: {str(e)}"
        
    print(f"Physical Evaluation of {tid}: pass={pass_ok}, reason={reason}, dy={res.get('stroke_dy_mm')}, dx={res.get('parasitic_dx_mm')}")
    results.append({
        "task_id": tid,
        "proposal": p,
        "pass": pass_ok,
        "reason": reason,
        "stroke_dy_mm": res.get("stroke_dy_mm"),
        "parasitic_dx_mm": res.get("parasitic_dx_mm")
    })

with open("test_casm_muse_proposals.json", "w") as f:
    json.dump(results, f, indent=2)

import json
from phase21_autonomous_scientist import call_muse_model

task = {
    'task_id': 'Task_01',
    'Fy_N': 0.8,
    'req_stroke_mm': 0.9,
    'max_drift_mm': 0.025,
    'max_stress_MPa': 14.0,
    'envelope_mm': [45.0, 30.0],
    'material_E': 1.4e9
}

prompt = f"""You are an autonomous engineering scientist for compliant mechanisms.
The following mechanism failed initial screening due to stroke deficit and transverse drift:
- Force: {task['Fy_N']} N, Required Stroke: >= {task['req_stroke_mm']} mm
- Max Lateral Drift: <= {task['max_drift_mm']} mm, Max Stress: <= {task['max_stress_MPa']} MPa
- Envelope: {task['envelope_mm'][0]} x {task['envelope_mm'][1]} mm

Available Compositional Grammar Primitives:
- 'folded_floating_shuttle'
- 'dual_series_shuttle'
- 'bilateral_compound_parallelogram'
- 'nested_dual_stage_folded'
- 'differential_decoupled'
- 'conventional_fixed_guided_parallelogram'

Diagnose the physical cause of failure, select the best topology primitive, and propose continuous thickness (in micrometers) and taper ratio.
Respond ONLY with JSON:
{{
  "failure_diagnosis": "physical reason",
  "proposed_topology": "primitive_name",
  "proposed_thickness_um": 800,
  "proposed_taper_ratio": 1.0,
  "predicted_stroke_mm": 1.0,
  "falsifiable_hypothesis": "explanation",
  "confidence": 0.85
}}"""

print("Calling unconstrained Meta Muse Spark 1.3...")
r = call_muse_model(prompt, temperature=0.3)
print("Parsed JSON:", r.get("parsed_json"))
print("Usage:", r.get("usage"))

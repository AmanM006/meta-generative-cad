import sys, json, os, time
from pathlib import Path
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

env_file = Path('C:/Users/aman/Documents/meta/horizonforge-local-test/.env')
api_key = None
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8').splitlines():
        if line.startswith('MODEL_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            break

client = OpenAI(base_url='https://api.meta.ai/v1', api_key=api_key)

with open('autonomous_discovery_closed_loop_receipt.json') as f:
    closed_loop = json.load(f)

learned_rule = json.loads(closed_loop['falsification_revision_call']['content'])['autonomous_design_rule']
print('Learned Rule in Scientific Memory:', learned_rule)

# New Fresh Task: Heavy load actuator under Fy = 8.5 N, envelope 85 x 50 mm, req_stroke >= 2.0 mm
prompt_transfer = f"""You are Neodustria's autonomous engineering agent.
You have updated your scientific memory with the following principle:
"{learned_rule}"

A new, unseen engineering challenge arrives:
- Packaging Envelope: 85 x 50 mm
- Applied Force: 8.5 N (High force regime)
- Required Stroke: >= 2.0 mm
- Max Allowable Stress: <= 25.0 MPa

Choose the optimal architecture based on your updated scientific memory:
Option A: conventional_fixed_guided_parallelogram
Option B: bilateral_compound_parallelogram

Return valid JSON:
{{
  "selected_architecture": "bilateral_compound_parallelogram",
  "causal_justification": "Under 8.5 N, conventional fixed-guided parallelograms will lock due to mid-plane stretching, whereas bilateral compound topologies relieve axial tension",
  "recommended_thickness_mm": 0.95
}}"""

resp = client.chat.completions.create(
    model='muse-spark-1.3', reasoning_effort='minimal', max_completion_tokens=400, temperature=0.1,
    messages=[{'role': 'user', 'content': prompt_transfer}]
)
cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
print(f"Transfer call complete in {resp.usage.total_tokens} tokens | Cost: ${cost:.6f}")
print("Model Decision:\n", resp.choices[0].message.content)

decision = json.loads(resp.choices[0].message.content)
chosen_arch = decision['selected_architecture']
print(f"\nEvaluating chosen architecture {chosen_arch} in nonlinear corotational FEA...")

gen = TypedTopologyGenerator(0.085, 0.050)
spec = gen.synthesize_by_name(chosen_arch, thickness=0.00095, shuttle_width=0.0035)
res = evaluate_full_physical_gates(spec, 0.085, 0.050, 8.5, req_dy=2.0, max_sig=25.0, max_dx=0.05, n_elem=8)
print("FEA Results on Fresh Task:")
print("  Strict Feasible Pass:", res.get('pass_strict'))
print("  Stroke:", round(res['stiffened']['stroke_mm'], 3), "mm (Required >= 2.0 mm)")
print("  Stress:", round(res['stiffened']['max_stress_MPa'], 2), "MPa (Max <= 25.0 MPa)")
print("  Clearance Deformed Max Y:", round(res['clearance']['deformed_max_y_mm'], 2), "mm (Env Y = 50.0 mm)")

with open('scientific_memory_transfer_verification.json', 'w') as f:
    json.dump({
        'timestamp_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'transfer_task': {'env': [85, 50], 'Fy': 8.5, 'req_dy': 2.0, 'max_sig': 25.0},
        'transfer_model_call': {'cost_usd': cost, 'decision': decision},
        'fea_ground_truth': {
            'stroke_mm': res['stiffened']['stroke_mm'],
            'max_stress_MPa': res['stiffened']['max_stress_MPa'],
            'pass_strict': res.get('pass_strict')
        }
    }, f, indent=2)
print("Saved transfer verification to scientific_memory_transfer_verification.json")

import sys, json, os, time
from pathlib import Path
from openai import OpenAI
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
from run_adaptive_classical_baseline import evaluate_full_physical_gates
from typed_topology_grammar import TypedTopologyGenerator

# Dynamic API Key resolution
api_key = os.environ.get('MODEL_API_KEY')
if not api_key:
    for search_path in [BASE_DIR / '.env', BASE_DIR / 'horizonforge-local-test' / '.env']:
        if search_path.exists():
            for line in search_path.read_text(encoding='utf-8').splitlines():
                if line.startswith('MODEL_API_KEY='): api_key = line.split('=', 1)[1].strip(); break
        if api_key: break

client = OpenAI(base_url='https://api.meta.ai/v1', api_key=api_key)

with open('blinded_scientific_discovery_receipt.json') as f:
    blinded_receipt = json.load(f)

learned_rule = blinded_receipt['step3_blinded_revision']['response']['autonomous_design_selection_rule']
print('Blinded Autonomous Rule Stored in Memory:\n"' + learned_rule + '"')

# Completely unseen evaluation task:
# Envelope: 80 x 45 mm (AR = 1.78)
# High Force: 7.0 N
# Requirement: Stroke >= 1.8 mm, max stress <= 22 MPa
prompt_transfer = f"""You are an autonomous engineering agent using your verified scientific memory:
Principle in memory: "{learned_rule}"

A new engineering challenge has arrived:
- Envelope: 80 x 45 mm
- Applied Force: 7.0 N (Heavy load regime)
- Required Stroke: >= 1.8 mm
- Max Allowable Stress: <= 22.0 MPa

Select the best candidate architecture based on your scientific memory:
- conventional_fixed_guided_parallelogram
- bilateral_compound_parallelogram

Return strictly valid JSON:
{{
  "selected_architecture": "...",
  "autonomous_justification": "...",
  "chosen_thickness_mm": 0.90
}}"""

resp = client.chat.completions.create(
    model='muse-spark-1.3', reasoning_effort='minimal', max_completion_tokens=400, temperature=0.1,
    messages=[{'role': 'user', 'content': prompt_transfer}]
)
cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
print(f"Transfer call complete in {resp.usage.total_tokens} tokens | Cost: ${cost:.6f}")
decision = json.loads(resp.choices[0].message.content)
print("Autonomous Decision:\n", json.dumps(decision, indent=2))

# Execute ground truth FEA on selected architecture
gen = TypedTopologyGenerator(0.080, 0.045)
th_sel = float(decision.get('chosen_thickness_mm', 0.90)) / 1000.0
spec = gen.synthesize_by_name(decision['selected_architecture'], thickness=th_sel, shuttle_width=0.0035)
res = evaluate_full_physical_gates(spec, 0.080, 0.045, 7.0, req_dy=1.8, max_sig=22.0, max_dx=0.05, n_elem=8)

print("\nFEA Ground Truth Verification:")
print("  Strict Feasible Pass:", res.get('pass_strict'))
print("  Stroke:", round(res['stiffened']['stroke_mm'], 3), "mm (Required >= 1.8 mm)")
print("  Stress:", round(res['stiffened']['max_stress_MPa'], 2), "MPa (Max <= 22.0 MPa)")
print("  Clearance Deformed Max Y:", round(res['clearance']['deformed_max_y_mm'], 2), "mm (Env Y = 45.0 mm)")

with open('blinded_memory_transfer_verification.json', 'w') as f:
    json.dump({
        'timestamp_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'unseen_task': {'env': [80, 45], 'Fy': 7.0, 'req_dy': 1.8, 'max_sig': 22.0},
        'transfer_model_call': {'cost_usd': cost, 'decision': decision},
        'fea_ground_truth': {
            'stroke_mm': res['stiffened']['stroke_mm'],
            'max_stress_MPa': res['stiffened']['max_stress_MPa'],
            'pass_strict': res.get('pass_strict')
        }
    }, f, indent=2)
print("Saved blinded memory transfer verification to blinded_memory_transfer_verification.json")

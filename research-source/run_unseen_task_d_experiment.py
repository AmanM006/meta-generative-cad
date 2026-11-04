import sys, json, time, numpy as np
from pathlib import Path
from openai import OpenAI
sys.path.insert(0, 'C:/Users/aman/Documents/meta/generative-engineering')
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

# Load API key
env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("MODEL_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key)

with open('C:/Users/aman/Documents/meta/UNSEEN_HELD_OUT_BENCHMARK.json') as f:
    benchmarks = json.load(f)

# Evaluate on Task D (80x40mm, Fy=3.5N, req>=2.50mm, stress<=22MPa, dx<=0.08mm)
task_name = 'Task D (High-Aspect Cantilever)'
cfg = benchmarks[task_name]
env_x = cfg['envelope_mm'][0] / 1000.0
env_y = cfg['envelope_mm'][1] / 1000.0
Fy = cfg['Fy_N']
req_dy = cfg['req_stroke_mm']
max_sig = cfg['max_stress_MPa']
max_dx = cfg['max_parasitic_dx_mm']

schema_prompt = """Return ONLY a valid JSON object matching:
{
  "topology_name": "string",
  "design_rationale": "string",
  "anchors": [[x, y], ...],
  "stages": [{"center": [x,y], "height": float, "thickness": float, "is_rigid": true, "ports": {"top": [x,y], "bot": [x,y]}}],
  "connections": [{"from_type": "anchor"|"stage", "from_index": int, "from_port": "center"|"top"|"bot", "to_type": "anchor"|"stage", "to_index": int, "to_port": "center"|"top"|"bot", "thickness": float}],
  "output_stage": int
}"""

prompt_cold = f"""You are an autonomous engineering scientist. Design a compliant flexure mechanism:
- Physical Envelope: X in [0.0, {env_x}] m, Y in [0.0, {env_y}] m, Z depth = 0.010 m.
- Input Force: {Fy} N in +Y direction at the output stage.
- Targets: Stroke dy >= {req_dy} mm, Peak stress <= {max_sig} MPa, Lateral drift |dx| <= {max_dx} mm.
- Material: PP (E=1.4 GPa, yield=35 MPa). Flexure thicknesses must be >= 0.00065 m.
{schema_prompt}"""

prompt_memory = f"""You are an autonomous engineering scientist. Design a compliant flexure mechanism:
- Physical Envelope: X in [0.0, {env_x}] m, Y in [0.0, {env_y}] m, Z depth = 0.010 m.
- Input Force: {Fy} N in +Y direction at the output stage.
- Targets: Stroke dy >= {req_dy} mm, Peak stress <= {max_sig} MPa, Lateral drift |dx| <= {max_dx} mm.
- Material: PP (E=1.4 GPa, yield=35 MPa). Flexure thicknesses must be >= 0.00065 m.

VERIFIED SCIENTIFIC PRINCIPLES:
1. PRIN-001 (Series Decoupling): In compact envelopes, single-stage blades suffer severe nonlinear chord-tension locking. Divide stroke across N series stages (intermediate shuttles) so each sub-stage undergoes small-angle deformation.
2. PRIN-002 (Bilateral Symmetric Parallelogram Guidance): Place parallel flexure pairs bilaterally symmetric about the central Y-axis. This identically cancels axial shift (dx) and rotation (theta).
3. PRIN-003 (Orthogonal Transverse Compliance): Flexure spans must run transverse to actuation (parallel to X-axis) to avoid compressive buckling under load.
4. PRIN-004 (Geometric Non-Crossing Invariance): Ensure no flexure lines cross. Provide clear packaging between shuttles.
{schema_prompt}"""

print(f"=== TESTING UNSEEN {task_name} ===")
seeds = [101, 202, 303]
results = {'cold_start': [], 'scientific_memory': []}

for seed in seeds:
    print(f"\n--- Seed {seed} ---")
    # Cold start call
    t0 = time.time()
    resp_cold = client.chat.completions.create(
        model="muse-spark-1.3",
        reasoning_effort="minimal",
        max_completion_tokens=4096,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt_cold}]
    )
    t_cold = time.time() - t0
    cost_cold = (resp_cold.usage.prompt_tokens * 0.20 + resp_cold.usage.completion_tokens * 0.80) / 1e6
    results['cold_start'].append({
        'seed': seed, 'runtime_s': t_cold, 'cost_usd': cost_cold, 'content': resp_cold.choices[0].message.content
    })
    print(f"Cold-Start Seed {seed} done in {t_cold:.1f}s, cost=${cost_cold:.5f}")

    # Scientific memory call
    t0 = time.time()
    resp_mem = client.chat.completions.create(
        model="muse-spark-1.3",
        reasoning_effort="minimal",
        max_completion_tokens=4096,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt_memory}]
    )
    t_mem = time.time() - t0
    cost_mem = (resp_mem.usage.prompt_tokens * 0.20 + resp_mem.usage.completion_tokens * 0.80) / 1e6
    results['scientific_memory'].append({
        'seed': seed, 'runtime_s': t_mem, 'cost_usd': cost_mem, 'content': resp_mem.choices[0].message.content
    })
    print(f"Memory Seed {seed} done in {t_mem:.1f}s, cost=${cost_mem:.5f}")

with open('C:/Users/aman/Documents/meta/unseen_task_d_multiseed_experiment.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nUnseen Task D Multi-Seed Experiment Complete!")

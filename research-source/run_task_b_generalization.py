import sys, json, os
from pathlib import Path
from openai import OpenAI

env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        for prefix in ("MODEL_API_KEY=", "META_API_KEY=", "META_MODEL_API_KEY="):
            if line.startswith(prefix):
                api_key = line.split("=", 1)[1].strip()
                break
        if api_key:
            break

if not api_key:
    print("Error: Could not load MODEL_API_KEY")
    sys.exit(1)

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key, max_retries=1, timeout=60)

schema = {
    "type": "object",
    "properties": {
        "topology_name": {"type": "string"},
        "design_rationale": {"type": "string"},
        "anchors": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
        "stages": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "center": {"type": "array", "items": {"type": "number"}},
                "height": {"type": "number"},
                "thickness": {"type": "number"},
                "is_rigid": {"type": "boolean"},
                "ports": {"type": "object", "additionalProperties": {"type": "array", "items": {"type": "number"}}}
            },
            "required": ["center", "height", "thickness", "ports"]
        }},
        "connections": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "from_type": {"type": "string", "enum": ["anchor", "stage"]},
                "from_index": {"type": "integer"},
                "from_port": {"type": "string"},
                "to_type": {"type": "string", "enum": ["anchor", "stage"]},
                "to_index": {"type": "integer"},
                "to_port": {"type": "string"},
                "thickness": {"type": "number"}
            },
            "required": ["from_type", "from_index", "from_port", "to_type", "to_index", "to_port", "thickness"]
        }},
        "output_stage": {"type": "integer"}
    },
    "required": ["topology_name", "design_rationale", "anchors", "stages", "connections", "output_stage"]
}

task_b_prompt_cold = """You are an autonomous engineering scientist specializing in compliant mechanisms.
Design a compliant flexure mechanism for TASK B:
- Physical Envelope: X in [0.0, 0.050] meters (50 mm), Y in [0.0, 0.035] meters (35 mm), Z depth = 0.010 m (10 mm).
- Input Actuation Force: 5.0 N point force applied in +Y direction at the output stage.
- Performance Targets: Actuation Stroke dy >= 1.500 mm (1500 microns), Peak stress <= 25.0 MPa, Parasitic drift |dx| <= 0.150 mm.
- Material: Polypropylene (E=1.4 GPa, yield=35 MPa). Flexure thicknesses must be between 0.0006 m and 0.0015 m.
Output valid JSON matching schema."""

task_b_prompt_memory = """You are an autonomous engineering scientist specializing in compliant mechanisms.
Design a compliant flexure mechanism for TASK B:
- Physical Envelope: X in [0.0, 0.050] meters (50 mm), Y in [0.0, 0.035] meters (35 mm), Z depth = 0.010 m (10 mm).
- Input Actuation Force: 5.0 N point force applied in +Y direction at the output stage.
- Performance Targets: Actuation Stroke dy >= 1.500 mm (1500 microns), Peak stress <= 25.0 MPa, Parasitic drift |dx| <= 0.150 mm.
- Material: Polypropylene (E=1.4 GPa, yield=35 MPa). Flexure thicknesses must be between 0.0006 m and 0.0015 m.

VERIFIED ENGINEERING SCIENTIFIC PRINCIPLES:
1. PRIN-001 (Orthogonal Series Decoupling): In compact envelopes, single-stage blades suffer severe nonlinear chord-tension stiffening (P ~ EA dy^2 / 2L^2). Connect intermediate floating shuttles in series so each sub-stage undergoes small angle deformation, doubling or tripling linear range.
2. PRIN-002 (Bilateral Symmetric Parallelogram Guidance): Place parallel flexure pairs bilaterally symmetric about the central Y-axis. This cancels axial shift (dx) and rotation (theta) identically.
3. PRIN-003 (Tangent Bifurcation Avoidance): Flexure spans must run transverse/orthogonal to the actuation direction (i.e. parallel to X-axis for Y-motion). Never orient blades along the compression axis under load.
4. PRIN-004 (Geometric Non-Crossing Invariance): Ensure no two flexure beam line segments cross or intersect. Keep distinct clearance between stages.
Output valid JSON matching schema."""

print('Calling Meta API for Task B Cold-Start...')
resp_cold = client.chat.completions.create(
    model='muse-spark-1.3',
    messages=[{'role': 'user', 'content': task_b_prompt_cold}],
    response_format={'type': 'json_object'},
    temperature=0.2,
    max_tokens=4096
)
prompt_toks_cold = getattr(resp_cold.usage, 'prompt_tokens', 250)
compl_toks_cold = getattr(resp_cold.usage, 'completion_tokens', 1500)
cost_cold = (prompt_toks_cold * 0.20 + compl_toks_cold * 0.80) / 1e6
print(f'Cold Start Done: {compl_toks_cold} tokens, cost=${cost_cold:.5f}')

print('Calling Meta API for Task B Scientific Memory...')
resp_mem = client.chat.completions.create(
    model='muse-spark-1.3',
    messages=[{'role': 'user', 'content': task_b_prompt_memory}],
    response_format={'type': 'json_object'},
    temperature=0.2,
    max_tokens=4096
)
prompt_toks_mem = getattr(resp_mem.usage, 'prompt_tokens', 350)
compl_toks_mem = getattr(resp_mem.usage, 'completion_tokens', 1500)
cost_mem = (prompt_toks_mem * 0.20 + compl_toks_mem * 0.80) / 1e6
print(f'Memory Done: {compl_toks_mem} tokens, cost=${cost_mem:.5f}')

results = [
    {'task': 'Task B (50x35mm, 5N, 1.5mm)', 'mode': 'cold_start_spark', 'cost': cost_cold, 'content': resp_cold.choices[0].message.content},
    {'task': 'Task B (50x35mm, 5N, 1.5mm)', 'mode': 'scientific_memory_spark', 'cost': cost_mem, 'content': resp_mem.choices[0].message.content}
]

with open('C:/Users/aman/Documents/meta/generalization_pilot_task_b.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'Task B Live Exploration Saved! Total Cost: ${(cost_cold + cost_mem):.5f}')

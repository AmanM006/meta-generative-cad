import sys, json, os, time
from pathlib import Path
from openai import OpenAI

env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("MODEL_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key, max_retries=1, timeout=60)

prompt_cold = """You are an autonomous engineering scientist specializing in compliant mechanisms.
Design a compliant flexure mechanism for TASK B:
- Physical Envelope: X in [0.0, 0.050] meters (50 mm), Y in [0.0, 0.035] meters (35 mm), Z depth = 0.010 m (10 mm).
- Input Actuation Force: 5.0 N point force applied in +Y direction at the output stage.
- Performance Targets: Actuation Stroke dy >= 1.500 mm (1500 microns), Peak stress <= 25.0 MPa, Parasitic drift |dx| <= 0.150 mm.
- Material: Polypropylene (E=1.4 GPa, yield=35 MPa). Flexure thicknesses must be between 0.0006 m and 0.0015 m.

Return ONLY a valid JSON object matching this schema:
{
  "topology_name": "string",
  "design_rationale": "string",
  "anchors": [[x, y], ...],
  "stages": [
    {"center": [x, y], "height": float, "thickness": float, "is_rigid": true, "ports": {"top": [x, y], "bot": [x, y]}}
  ],
  "connections": [
    {"from_type": "anchor"|"stage", "from_index": int, "from_port": "center"|"top"|"bot", "to_type": "anchor"|"stage", "to_index": int, "to_port": "center"|"top"|"bot", "thickness": float}
  ],
  "output_stage": int
}"""

prompt_memory = """You are an autonomous engineering scientist specializing in compliant mechanisms.
Design a compliant flexure mechanism for TASK B:
- Physical Envelope: X in [0.0, 0.050] meters (50 mm), Y in [0.0, 0.035] meters (35 mm), Z depth = 0.010 m (10 mm).
- Input Actuation Force: 5.0 N point force applied in +Y direction at the output stage.
- Performance Targets: Actuation Stroke dy >= 1.500 mm (1500 microns), Peak stress <= 25.0 MPa, Parasitic drift |dx| <= 0.150 mm.
- Material: Polypropylene (E=1.4 GPa, yield=35 MPa). Flexure thicknesses must be between 0.0006 m and 0.0015 m.

VERIFIED ENGINEERING SCIENTIFIC PRINCIPLES:
1. PRIN-001 (Orthogonal Series Decoupling): In compact envelopes, single-stage blades suffer severe nonlinear chord-tension stiffening (P ~ EA dy^2 / 2L^2). Connect intermediate floating shuttles in series so each sub-stage undergoes small angle deformation, multiplying linear range.
2. PRIN-002 (Bilateral Symmetric Parallelogram Guidance): Place parallel flexure pairs bilaterally symmetric about the central Y-axis. This cancels axial shift (dx) and rotation (theta) identically.
3. PRIN-003 (Tangent Bifurcation Avoidance): Flexure spans must run transverse/orthogonal to the actuation direction (i.e. parallel to X-axis for Y-motion). Never orient blades along the compression axis under load.
4. PRIN-004 (Geometric Non-Crossing Invariance): Ensure no two flexure beam line segments cross or intersect. Keep distinct clearance between stages.

Return ONLY a valid JSON object matching this schema:
{
  "topology_name": "string",
  "design_rationale": "string",
  "anchors": [[x, y], ...],
  "stages": [
    {"center": [x, y], "height": float, "thickness": float, "is_rigid": true, "ports": {"top": [x, y], "bot": [x, y]}}
  ],
  "connections": [
    {"from_type": "anchor"|"stage", "from_index": int, "from_port": "center"|"top"|"bot", "to_type": "anchor"|"stage", "to_index": int, "to_port": "center"|"top"|"bot", "thickness": float}
  ],
  "output_stage": int
}"""

print("Executing live Task B Cold-Start...")
resp_cold = client.chat.completions.create(
    model="muse-spark-1.3",
    reasoning_effort="minimal",
    max_completion_tokens=4096,
    temperature=0.2,
    messages=[{"role": "user", "content": prompt_cold}]
)
content_cold = resp_cold.choices[0].message.content
cost_cold = (resp_cold.usage.prompt_tokens * 0.20 + resp_cold.usage.completion_tokens * 0.80) / 1e6
print(f"Cold-Start complete: {resp_cold.usage.completion_tokens} tokens, cost=${cost_cold:.5f}")

print("Executing live Task B Scientific Memory...")
resp_mem = client.chat.completions.create(
    model="muse-spark-1.3",
    reasoning_effort="minimal",
    max_completion_tokens=4096,
    temperature=0.2,
    messages=[{"role": "user", "content": prompt_memory}]
)
content_mem = resp_mem.choices[0].message.content
cost_mem = (resp_mem.usage.prompt_tokens * 0.20 + resp_mem.usage.completion_tokens * 0.80) / 1e6
print(f"Scientific Memory complete: {resp_mem.usage.completion_tokens} tokens, cost=${cost_mem:.5f}")

results = [
    {
        "task": "Task B (50x35mm, 5N, 1.5mm)",
        "mode": "cold_start_spark",
        "tokens": resp_cold.usage.completion_tokens,
        "cost": cost_cold,
        "content": content_cold
    },
    {
        "task": "Task B (50x35mm, 5N, 1.5mm)",
        "mode": "scientific_memory_spark",
        "tokens": resp_mem.usage.completion_tokens,
        "cost": cost_mem,
        "content": content_mem
    }
]

with open("C:/Users/aman/Documents/meta/generalization_pilot_task_b.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Task B Generalization Pilot saved successfully. Total Cost: ${(cost_cold + cost_mem):.5f}")

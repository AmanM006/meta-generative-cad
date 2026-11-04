import sys, json, os, time
from pathlib import Path
from openai import OpenAI

env_file = Path('C:/Users/aman/Documents/meta/horizonforge-local-test/.env')
api_key = None
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8').splitlines():
        if line.startswith('MODEL_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            break

client = OpenAI(base_url='https://api.meta.ai/v1', api_key=api_key)

prompt = """You are Neodustria's autonomous scientific discovery agent.
An engineering challenge requires:
- Envelope: 95 x 55 mm
- Applied Transverse Force: 9.0 N (Heavy Load)
- Required Stroke: >= 2.2 mm
- Maximum Stress: <= 25.0 MPa
- Material: Polypropylene (E = 1.47 GPa, yield = 35.0 MPa)

Historical linear Euler-Bernoulli beam theory suggests that stroke is purely linear with force (delta proportional to F).
However, nonlinear corotational finite element analysis indicates that under 9.0 N, fixed-guided parallelograms exhibit severe chord-tension locking, whereas compound folded mechanisms relieve axial tension.

Please formulate two competing scientific hypotheses:
1. Hypothesis A (Conventional Fixed-Guided Parallelogram): Predict whether chord-tension locking will cause it to pass or fail the stroke requirement.
2. Hypothesis B (Bilateral Compound Parallelogram): Predict how intermediate shuttle translation affects axial chord tension and stroke yield.

Respond ONLY with valid JSON:
{
  "scientific_phenomenon": "Chord-Tension Locking vs Axial Stress Relief",
  "hypothesis_a": {
    "architecture": "conventional_fixed_guided_parallelogram",
    "predicted_response": "Severe sublinear stiffening due to mid-plane stretching; fails stroke requirement",
    "falsification_criterion": "Stroke < 2.2 mm or exponent alpha < 0.80 under 9.0 N"
  },
  "hypothesis_b": {
    "architecture": "bilateral_compound_parallelogram",
    "predicted_response": "Intermediate shuttle translates axially to relieve tension; achieves compliant stroke",
    "falsification_criterion": "Stroke >= 2.2 mm and max stress <= 25.0 MPa"
  },
  "experiment_design": {
    "discriminating_load_N": 9.0,
    "measurement": "output stroke, max stress, and deformed clearance"
  }
}"""

t0 = time.time()
resp = client.chat.completions.create(
    model='muse-spark-1.3',
    reasoning_effort='minimal',
    max_completion_tokens=1000,
    temperature=0.2,
    messages=[{'role': 'user', 'content': prompt}]
)
dt = time.time() - t0
cost = (resp.usage.prompt_tokens * 0.20 + resp.usage.completion_tokens * 0.80) / 1e6
print(f"Meta Muse Spark 1.3 responded in {dt:.2f}s | Cost: ${cost:.6f}")
print("Usage:", resp.usage)
content = resp.choices[0].message.content
print("\nModel Content:\n", content)

with open('muse_scientific_falsification_receipt.json', 'w') as f:
    json.dump({
        'timestamp_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'model': 'muse-spark-1.3',
        'prompt_tokens': resp.usage.prompt_tokens,
        'completion_tokens': resp.usage.completion_tokens,
        'cost_usd': cost,
        'raw_response': content
    }, f, indent=2)
print("Saved receipt to muse_scientific_falsification_receipt.json")

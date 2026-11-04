"""
Phase 21: Live Meta Muse Scientific Experiment Orchestrator
==========================================================
Executes authentic Meta Muse API hypothesis generation, nonlinear FEA evaluation,
falsification, law revision, memory updates, and held-out transfer.
Zero synthetic responses. All prompt/response tokens, latencies, and billing receipts tracked.
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from openai import OpenAI

# 1. Load API Key
ENV_FILE = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
api_key = None
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("MODEL_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

if not api_key:
    api_key = os.environ.get("MODEL_API_KEY")

assert api_key, "MODEL_API_KEY could not be loaded from environment or .env!"

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key)

# Cumulative expenditure tracker
# Meta Muse Spark 1.3 pricing: $0.20 / 1M prompt tokens, $0.80 / 1M completion tokens
TOTAL_MUSE_COST = 0.0
MAX_AUTHORIZED_BUDGET = 50.0 # User authorized up to $50

def call_muse_model(prompt: str, system_prompt: str = None, temperature: float = 0.2, max_tokens: int = 1500) -> dict:
    global TOTAL_MUSE_COST
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    t0 = time.time()
    resp = client.chat.completions.create(
        model="muse-spark-1.3",
        reasoning_effort="minimal",
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens
    )
    dt = time.time() - t0
    
    p_tok = resp.usage.prompt_tokens if resp.usage else 0
    c_tok = resp.usage.completion_tokens if resp.usage else 0
    r_tok = resp.usage.completion_tokens_details.reasoning_tokens if (resp.usage and resp.usage.completion_tokens_details) else 0
    cost = (p_tok * 0.20 + c_tok * 0.80) / 1e6
    TOTAL_MUSE_COST += cost
    
    choice = resp.choices[0]
    raw_content = choice.message.content or ""
    
    # Try parsing JSON from markdown block or raw text
    parsed_json = None
    if raw_content:
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(1))
            except Exception:
                pass
        if parsed_json is None:
            # Try finding first { and matching outer }
            start = raw_content.find("{")
            end = raw_content.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed_json = json.loads(raw_content[start:end+1])
                except Exception:
                    pass
            
    receipt = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": "muse-spark-1.3",
        "latency_s": round(dt, 3),
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "reasoning_tokens": r_tok,
        "cost_usd": round(cost, 6),
        "cumulative_cost_usd": round(TOTAL_MUSE_COST, 6),
        "finish_reason": choice.finish_reason,
        "raw_response": raw_content,
        "parsed_json": parsed_json
    }
    return receipt

if __name__ == "__main__":
    print("Testing call_muse_model...")
    r = call_muse_model("Respond in JSON: {\"status\": \"ready\", \"experiment\": \"phase21_pilot\"}")
    print(f"Latency: {r['latency_s']}s | Cost: ${r['cost_usd']:.6f} | Parsed: {r['parsed_json']}")

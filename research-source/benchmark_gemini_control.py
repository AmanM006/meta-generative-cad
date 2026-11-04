"""General-purpose LLM control on the frozen intent benchmark.

Requires GEMINI_API_KEY in the process environment. Never writes the key.
"""
import hashlib
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from benchmark_engineering_intent import prompt_for, score, screen
from engineering_intent import validate_model_interpretation
from open_ended_structural_discovery_engine import digest

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/intent_spec_confirmatory_frozen.json"
OUT = ROOT / "fresh_evidence/intent_spec_gemini_control_v2.json"
MODEL = "gemini-2.5-flash"


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is required in process environment")
    frozen = json.loads(FROZEN.read_text())
    if digest({k: v for k, v in frozen.items() if k != "sha256"}) != frozen["sha256"]:
        raise RuntimeError("Frozen benchmark checksum mismatch")
    state = json.loads(OUT.read_text()) if OUT.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(), "frozen_sha256": frozen["sha256"],
        "model": MODEL, "receipts": [], "results": {}}
    if state["frozen_sha256"] != frozen["sha256"]:
        raise RuntimeError("Existing ledger uses different benchmark")
    for case in frozen["held_out"]:
        if case["id"] in state["results"]:
            continue
        # Same schema, units, material data, and user request as Muse cold arm.
        prompt = prompt_for(case, False) + " The envelope_mm value must be [width_mm, height_mm], never a scalar."
        request_body = {"contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0, "maxOutputTokens": 1100,
                                             "responseMimeType": "application/json",
                                             "thinkingConfig": {"thinkingBudget": 0}}}
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            data=json.dumps(request_body).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
        start = time.perf_counter()
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.load(response)
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503) or attempt == 3:
                    raise
                time.sleep(2**attempt)
        raw = "".join(part.get("text", "") for part in payload["candidates"][0]["content"]["parts"])
        usage = payload.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        output_tokens = max(0, usage.get("totalTokenCount", 0) - prompt_tokens)
        receipt = {"request_id": payload.get("responseId"), "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                   "model": payload.get("modelVersion", MODEL), "request": request_body,
                   "request_sha256": digest(request_body), "response": raw,
                   "response_sha256": hashlib.sha256(raw.encode()).hexdigest(), "usage": usage,
                   "list_price_estimate_usd": (prompt_tokens*.30+output_tokens*2.50)/1e6,
                   "actual_billed_cost_usd": "UNKNOWN", "latency_s": time.perf_counter()-start,
                   "finish_reason": payload["candidates"][0].get("finishReason")}
        index = len(state["receipts"])
        state["receipts"].append(receipt)
        OUT.write_text(json.dumps(state, indent=2))
        try:
            parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
            candidate = validate_model_interpretation(case["request"], parsed)
            failure = None
        except (ValueError, TypeError) as exc:
            candidate, failure = None, str(exc)
        state["results"][case["id"]] = {"candidate": candidate, "receipt_index": index,
                                         "parse_or_validation_failure": failure,
                                         "score": score(candidate, case["reference"]),
                                         "physical_screen": screen(candidate, case["request"])}
        OUT.write_text(json.dumps(state, indent=2))
        print(case["id"], state["results"][case["id"]]["score"], flush=True)
        time.sleep(15)
    state["status"] = "COMPLETE"
    state["list_price_estimate_usd"] = sum(r["list_price_estimate_usd"] for r in state["receipts"])
    OUT.write_text(json.dumps(state, indent=2))
    print("COMPLETE estimated_list_price_usd", state["list_price_estimate_usd"])


if __name__ == "__main__":
    main()

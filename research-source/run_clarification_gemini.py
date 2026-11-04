"""Resumable Gemini control on the frozen clarification tasks.

Reads the user-supplied key from standard input. The key is never persisted.
"""
import hashlib
import getpass
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from open_ended_structural_discovery_engine import digest
from run_clarification_20 import FROZEN, metric, normalize, prompt_for

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "fresh_evidence/clarification_20_gemini_control.json"
MODEL = "gemini-2.5-flash"
MAX_ESTIMATED_USD = .15


def save(state):
    OUT.write_text(json.dumps(state, indent=2))


def main():
    key = (getpass.getpass("Gemini key: ") if sys.stdin.isatty() else sys.stdin.readline()).strip()
    if not key:
        raise RuntimeError("Gemini key required on standard input")
    frozen = json.loads(FROZEN.read_text())
    assert digest({k:v for k,v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    state = json.loads(OUT.read_text()) if OUT.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(), "frozen_sha256": frozen["sha256"],
        "model": MODEL, "receipts": [], "results": {}, "failures": []}
    assert state["frozen_sha256"] == frozen["sha256"]
    for case in frozen["cases"]:
        if case["id"] in state["results"]:
            continue
        if sum(x["estimated_cost_usd"] for x in state["receipts"]) >= MAX_ESTIMATED_USD-.01:
            state["status"] = "LOCAL_COST_CAP_REACHED"
            save(state)
            break
        prompt = prompt_for(case["request"], "muse_cold")
        request_body = {"contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0, "maxOutputTokens": 1400,
                                             "responseMimeType": "application/json",
                                             "thinkingConfig": {"thinkingBudget": 0}}}
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            data=json.dumps(request_body).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=70) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:1000]
            state["failures"].append({"case_id": case["id"], "http_status": exc.code,
                                      "request_sha256": digest(request_body), "body": body,
                                      "timestamp_utc": datetime.now(timezone.utc).isoformat()})
            state["status"] = "STOPPED_HTTP_" + str(exc.code)
            save(state)
            print("STOPPED", case["id"], exc.code, flush=True)
            break
        raw = "".join(part.get("text", "") for part in payload["candidates"][0]["content"]["parts"])
        usage = payload.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        output_tokens = max(0, usage.get("totalTokenCount", 0)-prompt_tokens)
        receipt = {"case_id": case["id"], "request_id": payload.get("responseId"),
                   "timestamp_utc": datetime.now(timezone.utc).isoformat(), "model": payload.get("modelVersion", MODEL),
                   "request": request_body, "request_sha256": digest(request_body),
                   "response": raw, "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                   "usage": usage, "estimated_cost_usd": (prompt_tokens*.30+output_tokens*2.50)/1e6,
                   "actual_billed_cost_usd": "UNKNOWN", "latency_s": time.perf_counter()-start,
                   "finish_reason": payload["candidates"][0].get("finishReason")}
        index = len(state["receipts"])
        state["receipts"].append(receipt)
        save(state)
        try:
            candidate, failure = normalize(raw), None
        except (ValueError, TypeError, KeyError) as exc:
            candidate, failure = None, str(exc)
        state["results"][case["id"]] = {"candidate": candidate, "receipt_index": index,
                                         "validation_failure": failure,
                                         "score": metric(candidate, case["reference"])}
        save(state)
        print(case["id"], state["results"][case["id"]]["score"]["full_case"], flush=True)
        time.sleep(15)
    else:
        state["status"] = "COMPLETE"
    state["estimated_new_usd"] = sum(x["estimated_cost_usd"] for x in state["receipts"])
    save(state)
    print("FINAL", state.get("status"), len(state["results"]), state["estimated_new_usd"], flush=True)


if __name__ == "__main__":
    main()

"""Opt-in one-call live verification; reads a local key, never prints it."""
import asyncio
import json
import os

import live_engineering_service as live
from run_clarification_20 import meta_key

REQUEST = "Design a PP guide for a 6 N load, 1.2 mm stroke, 75 x 50 mm package, drift under 0.03 mm, and stress under 20 MPa."
CODE = "local-verification-code"


async def main():
    key = meta_key()
    if not key:
        raise RuntimeError("Local Meta key unavailable")
    os.environ["MODEL_API_KEY"] = key
    os.environ["LIVE_DEMO_ACCESS_CODE"] = CODE
    started = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
    for _ in range(600):
        job = live.JOBS[started["id"]]
        if job["status"] in {"completed", "unresolved", "error", "abstained", "needs_clarification", "needs_manual_revision"}:
            print(json.dumps({
                "job_id": started["id"], "status": job["status"],
                "question": job.get("question"), "error": job.get("error"),
                "selected_mm": job.get("selected_mm"), "trial_count": len(job.get("trials", [])),
                "receipts": [{k: r.get(k) for k in ("request_id", "prompt_tokens", "completion_tokens", "estimated_cost_usd")} for r in job["receipts"]],
            }))
            return
        await asyncio.sleep(.5)
    raise TimeoutError("Live verification timed out")


if __name__ == "__main__":
    asyncio.run(main())

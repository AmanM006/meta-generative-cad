"""One bounded genuine Muse-directed repair on the known C01 development case."""
import asyncio
import json
import os

import live_engineering_service as live
from run_clarification_20 import meta_key

REQUEST = "Design a PP guide for a 6 N load, 1.2 mm stroke, 75 x 50 mm package, drift under 0.03 mm, and stress under 20 MPa."


async def main():
    key = meta_key()
    if not key:
        raise RuntimeError("Meta key unavailable")
    os.environ["MODEL_API_KEY"] = key
    os.environ["LIVE_DEMO_ACCESS_CODE"] = "local-r9-verification-code"
    started = await live.start(live.StartRequest(
        request_text=REQUEST, access_code="local-r9-verification-code", repair_mode="muse_directed"))
    for _ in range(900):
        job = live.JOBS[started["id"]]
        if job["status"] in {"completed", "unresolved", "error", "abstained", "needs_clarification"}:
            repair = job.get("repair_attempt") or {}
            print(json.dumps({
                "job_id": job["id"], "status": job["status"], "verdict": job.get("verdict"),
                "selection_source": job.get("selection_source"),
                "selected_design": job.get("selected_design"),
                "repair_verdict": repair.get("verdict"),
                "hypothesis": repair.get("hypothesis"),
                "prediction_check": repair.get("prediction_check"),
                "receipts": [{k: r.get(k) for k in ("request_id", "prompt_tokens", "completion_tokens", "estimated_cost_usd")} for r in job["receipts"]],
                "trial_count": len(job.get("trials", [])),
                "error": job.get("error"),
            }))
            return
        await asyncio.sleep(.5)
    raise TimeoutError("R9 local Muse repair did not finish")


if __name__ == "__main__":
    asyncio.run(main())

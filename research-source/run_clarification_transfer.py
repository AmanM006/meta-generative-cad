"""Single frozen transfer test of revised deterministic rules versus cold Muse."""
import json
from datetime import datetime, timezone
from pathlib import Path

from analyze_clarification_posthoc_rules import issue_codes
from engineering_intent import clarification, compile_intent
from open_ended_structural_discovery_engine import digest
from run_clarification_20 import metric, muse, normalize, prompt_for

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/clarification_transfer_12_frozen.json"
OUT = ROOT / "fresh_evidence/clarification_transfer_12_results.json"
MAPPED = {"ready_for_static_beam_screen": "proceed", "needs_clarification": "clarify",
          "contradictory": "abstain", "unsupported_physics": "abstain"}


def deterministic(text):
    interpretation = compile_intent(text)
    action = clarification(interpretation)
    return {"decision": MAPPED[interpretation["decision"]],
            "constraints": interpretation["constraints"],
            "missing": [x for x in interpretation["missing"] if x in ("material", "force_n", "stroke_min_mm", "envelope_mm")],
            "question_field": action.get("field"), "question": action.get("question"),
            "issue_codes": issue_codes(interpretation)}


def save(state):
    OUT.write_text(json.dumps(state, indent=2))


def main():
    frozen = json.loads(FROZEN.read_text())
    assert digest({k:v for k,v in frozen.items() if k != "sha256"}) == frozen["sha256"]
    state = json.loads(OUT.read_text()) if OUT.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(), "frozen_sha256": frozen["sha256"],
        "arms": ["revised_deterministic", "muse_cold"], "receipts": [], "results": {}}
    assert state["frozen_sha256"] == frozen["sha256"]
    for case in frozen["cases"]:
        for arm in state["arms"]:
            key = case["id"] + "/" + arm
            if key in state["results"]:
                continue
            if arm == "revised_deterministic":
                candidate, failure, index = deterministic(case["request"]), None, None
            else:
                raw, receipt = muse(prompt_for(case["request"], "muse_cold"), state)
                index = len(state["receipts"])
                state["receipts"].append(receipt)
                save(state)
                try:
                    candidate, failure = normalize(raw), None
                except (ValueError, TypeError, KeyError) as exc:
                    candidate, failure = None, str(exc)
            state["results"][key] = {"candidate": candidate, "validation_failure": failure,
                                     "receipt_index": index,
                                     "score": metric(candidate, case["reference"])}
            save(state)
            print(key, state["results"][key]["score"]["full_case"], flush=True)
    state["status"] = "COMPLETE"
    state["estimated_new_meta_usd"] = sum(x["estimated_cost_usd"] for x in state["receipts"])
    save(state)
    print("TRANSFER_COMPLETE", state["estimated_new_meta_usd"])


if __name__ == "__main__":
    main()

"""Development-only analysis of revised rules on the already seen 20 cases."""
import json
from pathlib import Path

from engineering_intent import compile_intent, clarification
from run_clarification_20 import metric

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / "fresh_evidence/clarification_20_frozen.json"
OUT = ROOT / "fresh_evidence/clarification_20_posthoc_rules.json"


def issue_codes(interpretation):
    phrases = " ".join(interpretation["contradictions"]+interpretation["unsupported"]+
                       interpretation.get("ambiguities", [])+interpretation.get("uncertainties", [])).lower()
    markers = {
        "conflicting_stroke": "conflicting stroke", "conflicting_drift": "conflicting lateral drift",
        "ambiguous_material": "material grade is ambiguous",
        "unsupported_manufacturing": "thickness below validated",
        "out_of_plane_loading": "out-of-plane", "uncertain_modulus": "material modulus must",
        "zero_force_positive_stroke": "zero load", "package_below_scale": "below the supported beam",
        "fatigue": "fatigue", "stress_above_yield": "exceeds listed material yield",
    }
    return [code for code, phrase in markers.items() if phrase in phrases]


def main():
    frozen = json.loads(FROZEN.read_text())
    rows = []
    mapped = {"ready_for_static_beam_screen": "proceed", "needs_clarification": "clarify",
              "contradictory": "abstain", "unsupported_physics": "abstain"}
    for case in frozen["cases"]:
        interpretation = compile_intent(case["request"])
        action = clarification(interpretation)
        candidate = {"decision": mapped[interpretation["decision"]],
                     "constraints": interpretation["constraints"],
                     "missing": [x for x in interpretation["missing"] if x in ("material", "force_n", "stroke_min_mm", "envelope_mm")],
                     "question_field": action.get("field"), "question": action.get("question"),
                     "issue_codes": issue_codes(interpretation)}
        rows.append({"id": case["id"], "candidate": candidate,
                     "score": metric(candidate, case["reference"])})
    result = {"status": "POSTHOC_DEVELOPMENT_ONLY", "frozen_sha256": frozen["sha256"],
              "warning": "Rules were modified after seeing the frozen benchmark; these are training-set scores, not a new held-out comparison",
              "full_cases": sum(x["score"]["full_case"] for x in rows),
              "decision_correct": sum(x["score"]["decision_correct"] for x in rows),
              "rows": rows}
    OUT.write_text(json.dumps(result, indent=2))
    print("POSTHOC", result["full_cases"], "/20", "decision", result["decision_correct"], "/20")
    print("FAILURES", [x["id"] for x in rows if not x["score"]["full_case"]])


if __name__ == "__main__":
    main()

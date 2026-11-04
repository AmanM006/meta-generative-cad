"""Write the one-time 20-case clarification benchmark before any model calls."""
import json
from pathlib import Path

from open_ended_structural_discovery_engine import digest

OUT = Path(__file__).resolve().parent / "fresh_evidence/clarification_20_frozen.json"


def case(ident, request, decision, question_field=None, *, material=None, force_n=None,
         stroke_min_mm=None, envelope_mm=None, drift_max_mm=None, stress_max_mpa=None,
         issue_codes=()):
    constraints = dict(material=material, force_n=force_n, stroke_min_mm=stroke_min_mm,
                       envelope_mm=envelope_mm, drift_max_mm=drift_max_mm,
                       stress_max_mpa=stress_max_mpa)
    missing = [key for key in ("material", "force_n", "stroke_min_mm", "envelope_mm")
               if constraints[key] is None]
    return {"id": ident, "request": request,
            "reference": {"decision": decision, "constraints": constraints,
                          "missing": missing, "question_field": question_field,
                          "issue_codes": list(issue_codes)}}


CASES = [
    case("Q01", "Design a polypropylene guide for 6 N force, at least 1.2 mm stroke, in a 75 x 50 mm package; drift below 0.03 mm and stress below 20 MPa.", "proceed", material="polypropylene", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], drift_max_mm=.03, stress_max_mpa=20),
    case("Q02", "A polypropylene guide must travel 1.2 mm in a 75 x 50 mm package; the actuation load has not been chosen.", "clarify", "force_n", material="polypropylene", stroke_min_mm=1.2, envelope_mm=[75,50]),
    case("Q03", "Build a PP stage carrying 6 N in a 75 x 50 mm package; required travel is still undecided.", "clarify", "stroke_min_mm", material="polypropylene", force_n=6, envelope_mm=[75,50]),
    case("Q04", "A compliant guide must carry 6 N, move at least 1.2 mm, and fit 75 x 50 mm; material is not specified.", "clarify", "material", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50]),
    case("Q05", "Design a polypropylene flexure under 6 N with at least 1.2 mm travel; the available package has not been measured.", "clarify", "envelope_mm", material="polypropylene", force_n=6, stroke_min_mm=1.2),
    case("Q06", "Use polypropylene at 6 N in a 75 x 50 mm package. The same output must have exactly 1.2 mm stroke and exactly 2.0 mm stroke under that load.", "abstain", material="polypropylene", force_n=6, envelope_mm=[75,50], issue_codes=("conflicting_stroke",)),
    case("Q07", "For a PP stage under 6 N, require 1.2 mm stroke in 75 x 50 mm; lateral drift must be below 0.01 mm and at least 0.05 mm in the same condition.", "abstain", material="polypropylene", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("conflicting_drift",)),
    case("Q08", "Can a PETG guide travel 1800 micrometers under 4000 mN within 88 x 58 mm, with drift under 0.05 mm?", "proceed", material="petg", force_n=4, stroke_min_mm=1.8, envelope_mm=[88,58], drift_max_mm=.05),
    case("Q09", "Build this guide from some plastic for a 6 N force, 1.2 mm stroke and 75 x 50 mm package; grade is unknown.", "clarify", "material", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("ambiguous_material",)),
    case("Q10", "Use PP under 6 N for 1.2 mm stroke within 75 x 50 mm. Every flexure must be only 0.1 mm thick although this solver requires at least 0.6 mm.", "abstain", material="polypropylene", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("unsupported_manufacturing",)),
    case("Q11", "Make a PP stage carrying 6 N with 1.2 mm stroke in 75 x 50 mm, but certify out-of-plane torsion resistance under that load.", "abstain", material="polypropylene", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("out_of_plane_loading",)),
    case("Q12", "Use recycled polypropylene for 6 N and 1.2 mm stroke in 75 x 50 mm; its elastic modulus is unknown and varies between batches.", "clarify", "material_properties", material="polypropylene", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("uncertain_modulus",)),
    case("Q13", "Design a compliant stage for 1.2 mm travel within 75 x 50 mm; both actuation force and material are undecided.", "clarify", "force_n", stroke_min_mm=1.2, envelope_mm=[75,50]),
    case("Q14", "I need a flexure in a 75 x 50 mm package, but force, required stroke, and material are not decided.", "clarify", "force_n", envelope_mm=[75,50]),
    case("Q15", "A 6 N, 1.2 mm guide must fit 75 x 50 mm. Choose between certified PP and certified PETG; I have not decided which grade to fabricate.", "clarify", "material", force_n=6, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("ambiguous_material",)),
    case("Q16", "A PP guide in a 75 x 50 mm package must move 1.2 mm when the only applied force is exactly 0 N.", "abstain", material="polypropylene", force_n=0, stroke_min_mm=1.2, envelope_mm=[75,50], issue_codes=("zero_force_positive_stroke",)),
    case("Q17", "Fit a polypropylene 3 N guide with 1 mm stroke into a 12 x 8 mm package using the validated beam template.", "abstain", material="polypropylene", force_n=3, stroke_min_mm=1, envelope_mm=[12,8], issue_codes=("package_below_scale",)),
    case("Q18", "A PETG guide must withstand 4 N, move 1.8 mm in 88 x 58 mm, and be certified for one million fatigue cycles.", "abstain", material="petg", force_n=4, stroke_min_mm=1.8, envelope_mm=[88,58], issue_codes=("fatigue",)),
    case("Q19", "Design an aluminum stage at 2 N, 1 mm stroke, 70 x 50 mm, with acceptable stress as high as 300 MPa despite listed yield of 240 MPa.", "abstain", material="aluminum", force_n=2, stroke_min_mm=1, envelope_mm=[70,50], stress_max_mpa=300, issue_codes=("stress_above_yield",)),
    case("Q20", "For PETG, design 1.8 mm travel under 4 N inside an 88 x 58 mm envelope. No drift tolerance has been imposed.", "proceed", material="petg", force_n=4, stroke_min_mm=1.8, envelope_mm=[88,58]),
]


def main():
    if OUT.exists():
        raise SystemExit("Frozen benchmark already exists; refusing to overwrite")
    body = {"title": "Predeclared 20-case engineering clarification challenge",
            "scope": "2D static beam problem formulation; simulated user requests, not live conversations",
            "question_priority": ["force_n", "stroke_min_mm", "material", "envelope_mm"],
            "scoring": {"full_case": "decision, all six fields, missing required fields, primary question and issue codes must match",
                        "unsafe_assumption": "any non-null value for an absent field is a failure",
                        "model_invalid": "retained in denominator as failure"},
            "cases": CASES}
    body["sha256"] = digest(body)
    OUT.write_text(json.dumps(body, indent=2))
    print("FROZEN", len(CASES), body["sha256"])


if __name__ == "__main__":
    main()

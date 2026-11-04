"""Freeze one new transfer set to test revised rules against cold Muse."""
import json
from pathlib import Path

from freeze_clarification_benchmark import case
from open_ended_structural_discovery_engine import digest

OUT = Path(__file__).resolve().parent / "fresh_evidence/clarification_transfer_12_frozen.json"

CASES = [
    case("T01", "Please size a PETG guide for 2500 mN of actuation and 1500 micrometers of travel in an 82 x 54 mm box. Side drift may not exceed 40 micrometers.", "proceed", material="petg", force_n=2.5, stroke_min_mm=1.5, envelope_mm=[82,54], drift_max_mm=.04),
    case("T02", "A PP guide needs 1.5 mm of motion inside 80 x 55 mm. Keep drift below 0.04 mm and stress below 18 MPa. We have not specified its operating force.", "clarify", "force_n", material="polypropylene", stroke_min_mm=1.5, envelope_mm=[80,55], drift_max_mm=.04, stress_max_mpa=18),
    case("T03", "An aluminum flexure carries 3 N within 100 x 70 mm and must stay below 80 MPa. Required output displacement has not been selected.", "clarify", "stroke_min_mm", material="aluminum", force_n=3, envelope_mm=[100,70], stress_max_mpa=80),
    case("T04", "The stage must withstand 5 N, produce at least 1 mm travel, and fit an 80 x 55 mm footprint. No material has been chosen.", "clarify", "material", force_n=5, stroke_min_mm=1, envelope_mm=[80,55]),
    case("T05", "Design a PP beam guide at 6 N and 1 mm minimum travel. Available package dimensions have not been measured.", "clarify", "envelope_mm", material="polypropylene", force_n=6, stroke_min_mm=1),
    case("T06", "In the same 5 N test, a PP carriage in 80 x 55 mm must move at least 2 mm and at most 1 mm; both limits are mandatory.", "abstain", material="polypropylene", force_n=5, stroke_min_mm=2, envelope_mm=[80,55], issue_codes=("conflicting_stroke",)),
    case("T07", "Make a PETG 4 N, 1 mm stage in 80 x 55 mm, but require every flexure to be 0.2 mm thick even though the validated minimum is 0.6 mm.", "abstain", material="petg", force_n=4, stroke_min_mm=1, envelope_mm=[80,55], issue_codes=("unsupported_manufacturing",)),
    case("T08", "A PP stage needs 4 N, 1 mm stroke and an 80 x 55 mm envelope. Certify its out-of-plane bending under the same load.", "abstain", material="polypropylene", force_n=4, stroke_min_mm=1, envelope_mm=[80,55], issue_codes=("out_of_plane_loading",)),
    case("T09", "For a recycled PP batch, build a 4 N guide with 1 mm travel in 80 x 55 mm. Its elastic modulus is unknown until material testing.", "clarify", "material_properties", material="polypropylene", force_n=4, stroke_min_mm=1, envelope_mm=[80,55], issue_codes=("uncertain_modulus",)),
    case("T10", "Build a 4 N, 1 mm guide inside 80 x 55 mm. The production choice is either PP or PETG, and neither has been selected.", "clarify", "material", force_n=4, stroke_min_mm=1, envelope_mm=[80,55], issue_codes=("ambiguous_material",)),
    case("T11", "A PP mechanism must carry 3 N and travel 1 mm inside a 14 x 9 mm package, below the validated geometry scale.", "abstain", material="polypropylene", force_n=3, stroke_min_mm=1, envelope_mm=[14,9], issue_codes=("package_below_scale",)),
    case("T12", "Specify a PP guide for 2 N and 1 mm minimum output travel in an 80 x 55 mm envelope. No drift or stress limits were imposed.", "proceed", material="polypropylene", force_n=2, stroke_min_mm=1, envelope_mm=[80,55]),
]


def main():
    if OUT.exists():
        raise SystemExit("Frozen transfer set exists; refusing overwrite")
    body = {"title": "Single unseen-language transfer challenge for revised rules versus cold Muse",
            "scope": "Project-authored 12 requests; frozen after first benchmark and rules revision",
            "scoring": "Same exact-case rubric and schema as clarification_20_frozen.json",
            "cases": CASES}
    body["sha256"] = digest(body)
    OUT.write_text(json.dumps(body, indent=2))
    print("TRANSFER_FROZEN", len(CASES), body["sha256"])


if __name__ == "__main__":
    main()

"""Fail-closed engineering-intent compiler for the supported static beam domain."""
import re
from dataclasses import dataclass, asdict

MATERIALS = {
    "polypropylene": {"E_pa": 1.4e9, "yield_strength_pa": 35e6},
    "petg": {"E_pa": 2.1e9, "yield_strength_pa": 45e6},
    "aluminum": {"E_pa": 69e9, "yield_strength_pa": 240e6},
}
UNSUPPORTED = ("snap-through", "bistable", "fatigue", "thermal cycling", "vibration", "impact", "buckling load", "out-of-plane", "out of plane", "torsion resistance")


def _number(text, patterns, scale=1.0):
    for pattern in patterns:
        found = re.search(pattern, text, re.I)
        if found:
            return round(float(found.group(1)) * scale, 9)
    return None


def compile_intent(text):
    """Extract explicit constraints only. Missing fields remain unknown."""
    if not isinstance(text, str) or not (10 <= len(text) <= 2000):
        raise ValueError("Request must contain 10–2000 characters")
    t = text.lower().replace("μ", "µ")
    mentioned = {m for m in MATERIALS if re.search(r"\b" + m + r"\b", t)}
    if re.search(r"\bpp\b", t):
        mentioned.add("polypropylene")
    material = next(iter(mentioned)) if len(mentioned) == 1 else None
    ambiguities = []
    if len(mentioned) > 1 or re.search(r"\b(?:some plastic|unknown grade|grade is unknown)\b", t):
        material = None
        ambiguities.append("Material grade is ambiguous")
    force = _number(t, [r"(?:load|force|under|at|with)\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*n\b",
                        r"(\d+(?:\.\d+)?)\s*n\b\s*(?:load|force)"])
    if force is None:
        force = _number(t, [r"(?:load|force|under|at|with)\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*mn\b"], .001)
    if force is None:
        found_force = re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)\s*n\b", t)
        if len(found_force) == 1:
            force = float(found_force[0])
    stroke = _number(t, [r"(?:stroke|travel|displacement|move|motion)\s*(?:of|at least|>=|≥|by)?\s*(\d+(?:\.\d+)?)\s*mm\b",
                         r"(\d+(?:\.\d+)?)\s*mm\b\s*(?:stroke|travel|displacement|motion)"])
    if stroke is None:
        stroke = _number(t, [r"(?:stroke|travel|displacement|move|motion)\s*(?:of|at least|>=|≥|by)?\s*(\d+(?:\.\d+)?)\s*(?:µm|um|micrometers?)\b",
                             r"(\d+(?:\.\d+)?)\s*(?:µm|um|micrometers?)\b\s*(?:stroke|travel|displacement)"], .001)
    envelope = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm)?\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm\b", t)
    envelope_mm = [float(envelope.group(1)), float(envelope.group(2))] if envelope else None
    drift = _number(t, [r"(?:lateral\s*)?(?:drift|shift|parasitic\s*motion)\s*(?:below|under|<=|≤|less than|limit|to|of)?\s*(\d+(?:\.\d+)?)\s*mm\b",
                        r"(\d+(?:\.\d+)?)\s*mm\b\s*(?:max\s*)?(?:lateral\s*)?drift"])
    stress = _number(t, [r"(?:stress|von mises)\s*(?:below|under|<=|≤|less than|limit|to|of|as high as)?\s*(\d+(?:\.\d+)?)\s*mpa\b",
                         r"(\d+(?:\.\d+)?)\s*mpa\b\s*(?:max\s*)?stress"])
    values = {"material": material, "force_n": force, "stroke_min_mm": stroke,
              "envelope_mm": envelope_mm, "drift_max_mm": drift, "stress_max_mpa": stress}
    missing = [key for key in ("material", "force_n", "stroke_min_mm", "envelope_mm") if values[key] is None]
    unsupported = [term for term in UNSUPPORTED if term in t]
    contradictions = []
    stroke_values = {float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*mm\s*(?:stroke|travel|displacement)\b", t)}
    if len(stroke_values) > 1 and ("exactly" in t or "same output" in t):
        contradictions.append("Conflicting stroke values under the same load")
        stroke = None
        values["stroke_min_mm"] = None
        if "stroke_min_mm" not in missing:
            missing.append("stroke_min_mm")
    drift_conflict = re.search(r"drift.{0,50}?(?:below|under|<=|≤)\s*(\d+(?:\.\d+)?)\s*mm.{0,40}?(?:at least|above|>=|≥)\s*(\d+(?:\.\d+)?)\s*mm", t)
    if drift_conflict and float(drift_conflict.group(2)) >= float(drift_conflict.group(1)):
        contradictions.append("Conflicting lateral drift bounds")
        drift = None
        values["drift_max_mm"] = None
    thicknesses = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*mm\s*thick\b", t)]
    if any(x < .6 for x in thicknesses):
        contradictions.append("Requested flexure thickness below validated 0.6 mm minimum")
    if force is not None and force <= 0 and stroke is not None and stroke > 0:
        contradictions.append("Positive actuation stroke requested with zero load")
    if envelope_mm and stroke is not None and stroke >= envelope_mm[1]:
        contradictions.append("Requested stroke equals or exceeds package height")
    if envelope_mm and (envelope_mm[0] < 15 or envelope_mm[1] < 10):
        contradictions.append("Package is below the supported beam geometry scale")
    if stress is not None and material and stress > MATERIALS[material]["yield_strength_pa"]/1e6:
        contradictions.append("Stress limit exceeds listed material yield strength")
    uncertainties = []
    measured_modulus = _number(t, [r"measured\s+(?:elastic\s+)?modulus\s*(?:of|is|=)?\s*(\d+(?:\.\d+)?)\s*gpa\b"])
    if measured_modulus is not None and measured_modulus <= 0:
        contradictions.append("Measured elastic modulus must be positive")
    if measured_modulus is None and re.search(r"(?:elastic\s+)?modulus.{0,30}?(?:unknown|varies|uncertain)", t):
        uncertainties.append("Material modulus must be measured or specified for this batch")
        missing.append("material_properties")
    if unsupported:
        decision = "unsupported_physics"
    elif contradictions:
        decision = "contradictory"
    elif missing:
        decision = "needs_clarification"
    else:
        decision = "ready_for_static_beam_screen"
    return {"decision": decision, "constraints": values, "missing": missing,
            "contradictions": contradictions, "unsupported": unsupported,
            "ambiguities": ambiguities, "uncertainties": uncertainties,
            "material_properties": {"measured_E_gpa": measured_modulus},
            "provenance": "deterministic_text_parser", "solver_scope": "2D static nonlinear beam screening only"}


QUESTION_ORDER = ("force_n", "stroke_min_mm", "material", "envelope_mm", "material_properties")
QUESTIONS = {
    "force_n": "What actuation force, in N, must the mechanism carry?",
    "stroke_min_mm": "What minimum output stroke, in mm, is required?",
    "material": "Which validated material will be used: polypropylene, PETG, or aluminum?",
    "envelope_mm": "What is the available width × height, in mm?",
    "material_properties": "What measured elastic modulus, in GPa, applies to the actual material batch?",
}


def clarification(interpretation):
    """Select one question without supplying a missing engineering value."""
    decision = interpretation["decision"]
    if decision == "unsupported_physics":
        return {"action": "abstain", "question": None,
                "reason": "The stated physics is outside the validated 2D static beam solver."}
    if decision == "contradictory":
        return {"action": "abstain", "question": None,
                "reason": "; ".join(interpretation["contradictions"])}
    if decision == "ready_for_static_beam_screen":
        return {"action": "proceed", "question": None,
                "reason": "Required geometry, load, motion, and material are explicit."}
    missing = set(interpretation["missing"])
    field = next(key for key in QUESTION_ORDER if key in missing)
    return {"action": "clarify", "field": field, "question": QUESTIONS[field],
            "remaining_required": [key for key in QUESTION_ORDER if key in missing],
            "reason": "Required physical input is absent; no value has been assumed.",
            "ranking_provenance": "predeclared engineering priority; no numerical sensitivity calculation"}


def validate_model_interpretation(text, candidate):
    """Validate schema and numeric ranges; never silently fill absent constraints."""
    if not isinstance(candidate, dict) or not isinstance(candidate.get("constraints"), dict):
        raise ValueError("Model output lacks constraints object")
    c = candidate["constraints"]
    allowed = {"material", "force_n", "stroke_min_mm", "envelope_mm", "drift_max_mm", "stress_max_mpa"}
    if set(c) != allowed:
        raise ValueError("Constraint keys mismatch")
    if isinstance(c["material"], str):
        label = c["material"].strip().lower()
        c["material"] = "polypropylene" if label == "pp" else label
    if c["material"] is not None and c["material"] not in MATERIALS:
        raise ValueError("Unsupported material label")
    for key in ("force_n", "stroke_min_mm", "drift_max_mm", "stress_max_mpa"):
        value = c[key]
        if value is not None and (not isinstance(value, (int, float)) or not 0 <= value <= 1e5):
            raise ValueError("Invalid numeric constraint: " + key)
    e = c["envelope_mm"]
    if e is not None and (not isinstance(e, list) or len(e) != 2 or
                          any(not isinstance(v, (int, float)) or not 0 < v <= 1000 for v in e)):
        raise ValueError("Invalid envelope")
    if candidate.get("decision") not in {"unsupported_physics", "contradictory", "needs_clarification", "ready_for_static_beam_screen"}:
        raise ValueError("Invalid decision")
    missing = [k for k in ("material", "force_n", "stroke_min_mm", "envelope_mm") if c[k] is None]
    if candidate["decision"] == "ready_for_static_beam_screen" and missing:
        raise ValueError("Ready decision has missing required values")
    return candidate

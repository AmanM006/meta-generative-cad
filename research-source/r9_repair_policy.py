"""Strict menu for one Muse-directed beam experiment after measured failure."""
import copy
import json
import math

from open_ended_structural_discovery_engine import validate_proposal

ACTIONS = {
    "uniform_plus_0p1": tuple(range(6)),
    "outer_plus_0p1": (0, 1, 2, 3),
    "bridge_plus_0p1": (4, 5),
}
DIRECTIONS = {"increase", "decrease", "unchanged"}


def failure_metrics(result, task):
    if not all(key in result for key in ("stroke_mm", "absolute_drift_mm", "stress_mpa", "gates")):
        smallest = min(edge["thickness"] for edge in result["proposal"]["connections"]) * 1000
        floor = task["min_flexure_thickness_m"] * 1000
        return {"failed_gates": ["manufacturing_floor"],
                "minimum_thickness_mm": floor, "actual_min_thickness_mm": smallest,
                "thickness_margin_mm": smallest - floor,
                "stroke_mm": None, "absolute_drift_mm": None, "stress_mpa": None,
                "reason": "Corner geometry rejected before FEA; no numerical response exists"}
    return {
        "stroke_mm": result["stroke_mm"],
        "required_stroke_mm": task["stroke_min_mm"],
        "stroke_margin_mm": result["stroke_mm"] - task["stroke_min_mm"],
        "absolute_drift_mm": result["absolute_drift_mm"],
        "drift_limit_mm": task["drift_max_mm"],
        "drift_margin_mm": task["drift_max_mm"] - result["absolute_drift_mm"],
        "stress_mpa": result["stress_mpa"],
        "stress_limit_mpa": task["stress_max_mpa"],
        "stress_margin_mpa": task["stress_max_mpa"] - result["stress_mpa"],
        "failed_gates": sorted(k for k, passed in result["gates"].items() if not passed),
    }


def casm_context(spec):
    """Retrieve bounded, task-matched stored principles; no current-case verdict."""
    from casm_scalable_engine import ScalableCASMEngine
    c = spec["constraints"]
    retrieved = ScalableCASMEngine().query_scalable_memory(
        c["envelope_mm"][0], c["envelope_mm"][1], c["force_n"], c["stroke_min_mm"])
    return {"applicable": [{"id": x["id"], "physics": x["physics"]} for x in retrieved["applicable"][:3]],
            "rejected": [{"id": x["id"], "reasons": x["reasons"]} for x in retrieved["rejected"][:3]],
            "warning": "Historical retrieval only; no current-case physics pass is implied"}


def repair_prompt(spec, failure, base_thickness_mm, validated_memory=False, casm_memory=False):
    context = {
        "task": spec["constraints"], "base_uniform_thickness_mm": base_thickness_mm,
        "observed_failure": failure,
        "allowed_experiments": {
            "uniform_plus_0p1": "increase all six beam thicknesses by 0.1 mm",
            "outer_plus_0p1": "increase four anchor-to-stage beams by 0.1 mm",
            "bridge_plus_0p1": "increase two interstage beams by 0.1 mm",
        },
    }
    if casm_memory:
        context["retrieved_casm_memory"] = casm_context(spec)
    memory = ("Prior validated observation: uniform thickening can lower lateral drift but may also lower stroke. "
              "Treat this as a hypothesis, not a result for the present task. ") if validated_memory else ""
    return (
        "You are choosing ONE next engineering experiment after a measured beam failure or compiler geometry rejection. "
        + memory + "Use only the observed failure and allowed experiments below. "
        "Return one JSON object with EXACT keys: diagnosis, failed_gate, action, "
        "predicted_stroke_direction, predicted_drift_direction. "
        "The failed_gate must be one of observed_failure.failed_gates. "
        "Action must be one of the allowed experiment IDs. Directions must each be "
        "increase, decrease, or unchanged relative to the measured failed uncertainty corner under the same perturbation. "
        "If that corner was rejected before FEA, direction predictions cannot be scored and are only hypotheses. "
        "Do not invent numerical solver outputs, extra keys, or a success claim. "
        "Explain the physical load path in diagnosis (20-300 characters).\n"
        + json.dumps(context, sort_keys=True)
    )


def parse_repair(raw, failed_gates):
    value = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    required = {"diagnosis", "failed_gate", "action", "predicted_stroke_direction", "predicted_drift_direction"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("Repair response schema")
    if not isinstance(value["diagnosis"], str) or not (20 <= len(value["diagnosis"]) <= 300):
        raise ValueError("Repair diagnosis length")
    if value["failed_gate"] not in failed_gates:
        raise ValueError("Repair diagnosis does not name an actual failed gate")
    if value["action"] not in ACTIONS:
        raise ValueError("Repair action outside predeclared menu")
    if value["predicted_stroke_direction"] not in DIRECTIONS or value["predicted_drift_direction"] not in DIRECTIONS:
        raise ValueError("Repair direction enum")
    return value


def mutate(proposal, action):
    if action not in ACTIONS or len(proposal["connections"]) != 6:
        raise ValueError("Repair action or geometry outside menu")
    changed = copy.deepcopy(proposal)
    for index in ACTIONS[action]:
        old = changed["connections"][index]["thickness"]
        new = round(old + .0001, 7)
        if not math.isfinite(new) or new > .0010:
            raise ValueError("Repair action exceeds 1.0 mm evaluated family limit")
        changed["connections"][index]["thickness"] = new
    validate_proposal(changed)
    return changed


def measured_direction(before, after, tolerance=1e-5):
    delta = after - before
    return "unchanged" if abs(delta) <= tolerance else "increase" if delta > 0 else "decrease"

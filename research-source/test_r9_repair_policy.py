import copy
import json

import pytest

from r9_repair_policy import casm_context, failure_metrics, measured_direction, mutate, parse_repair, repair_prompt


@pytest.fixture
def graph():
    source = json.load(open("fresh_evidence/intent_spec_confirmatory_results.json"))
    proposal = copy.deepcopy(source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"])
    for edge in proposal["connections"]:
        edge["thickness"] = .0009
    return proposal


def test_mutation_changes_only_declared_edges(graph):
    outer = mutate(graph, "outer_plus_0p1")
    assert [round(edge["thickness"] * 1000, 1) for edge in outer["connections"]] == [1, 1, 1, 1, .9, .9]
    assert all(edge["thickness"] == .0009 for edge in graph["connections"])
    with pytest.raises(ValueError):
        mutate(outer, "outer_plus_0p1")


def test_strict_model_schema_rejects_invented_outputs():
    valid = {"diagnosis": "The failed corner exceeds lateral drift because the outer beams bend.",
             "failed_gate": "absolute_drift", "action": "outer_plus_0p1",
             "predicted_stroke_direction": "decrease", "predicted_drift_direction": "decrease"}
    assert parse_repair(json.dumps(valid), ["absolute_drift"]) == valid
    with pytest.raises(ValueError):
        parse_repair(json.dumps({**valid, "predicted_drift_mm": .01}), ["absolute_drift"])
    with pytest.raises(ValueError):
        parse_repair(json.dumps({**valid, "failed_gate": "stress"}), ["absolute_drift"])
    assert measured_direction(.03, .02) == "decrease"


def test_casm_retrieval_is_context_not_current_case_result():
    spec = {"constraints": {"material": "polypropylene", "force_n": 6, "stroke_min_mm": 1.2,
                            "envelope_mm": [75, 50], "drift_max_mm": .03, "stress_max_mpa": 20}}
    memory = casm_context(spec)
    assert memory["applicable"] and "no current-case physics pass" in memory["warning"]
    prompt = repair_prompt(spec, {"failed_gates": ["absolute_drift"]}, .9, casm_memory=True)
    assert "retrieved_casm_memory" in prompt and "Do not invent numerical solver outputs" in prompt


def test_rejected_tolerance_corner_reports_geometry_margin_without_fea_values():
    evidence = json.load(open("fresh_evidence/r9_generalization_results.json"))
    corner = evidence["cases"]["G01_low_force_precision"]["trials"][0]["joint_corners"][0]
    failure = failure_metrics(corner["result"], corner["task"])
    assert failure["failed_gates"] == ["manufacturing_floor"]
    assert failure["thickness_margin_mm"] == pytest.approx(-.03)
    assert failure["stroke_mm"] is None

"""Mutation checks for the frozen R9.1 evidence auditor."""
import json
from pathlib import Path

import pytest

from audit_r91_matched import ROOT, main, validate_significance_claim


@pytest.fixture
def evidence(tmp_path):
    for source in ROOT.glob("r91_*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    return tmp_path


def mutate(path: Path, change):
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value))


def test_original_evidence_passes(evidence):
    assert main(evidence, write=False)["arms"]["D"]["repair_passes"] == 4


def test_frozen_task_mutation_rejected(evidence):
    mutate(evidence / "r91_frozen_tasks.json", lambda x: x["cases"][0]["constraints"].update({"load_n": 99}))
    with pytest.raises(AssertionError):
        main(evidence, write=False)


def test_solver_measurement_mutation_rejected(evidence):
    path = evidence / "r91_arm_D.json"
    def change(x):
        x["cases"]["T10"]["measured"]["candidate"]["fine"]["stroke_mm"] = -1
    mutate(path, change)
    with pytest.raises(AssertionError):
        main(evidence, write=False)


def test_model_response_mutation_rejected(evidence):
    mutate(evidence / "r91_arm_D.json", lambda x: x["cases"]["T10"]["model_receipt"].update({"response": "tampered"}))
    with pytest.raises(AssertionError):
        main(evidence, write=False)


def test_missing_receipt_rejected(evidence):
    mutate(evidence / "r91_arm_D.json", lambda x: x["cases"]["T10"].update({"model_receipt": None}))
    with pytest.raises(AssertionError):
        main(evidence, write=False)


def test_false_success_rejected(evidence):
    mutate(evidence / "r91_arm_D.json", lambda x: x["cases"]["T10"].update({"one_step_robust": False}))
    with pytest.raises(AssertionError):
        main(evidence, write=False)


def test_false_significance_rejected(evidence):
    comparisons = main(evidence, write=False)["paired_comparisons"]
    with pytest.raises(AssertionError):
        validate_significance_claim(comparisons, "D_vs_B", True)

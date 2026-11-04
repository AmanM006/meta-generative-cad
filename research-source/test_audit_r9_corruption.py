"""Deliberately corrupt independent evidence and require the R9 audit to fail."""
import json
import shutil

import pytest

from audit_r9_matched import ROOT, main

FILES = ["r9_frozen_tasks.json", "r9_matched_protocol.json", "r9_generalization_results.json",
         *(f"r9_arm_{arm}.json" for arm in "BCDE")]


def copy_evidence(tmp_path):
    for name in FILES:
        shutil.copyfile(ROOT / name, tmp_path / name)
    return tmp_path


def rewrite(path, change):
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value))


def test_original_audit_passes():
    assert main(write=False)["arms"]["D"]["repair_passes"] == 5


def test_corrupt_receipt_token_accounting_is_rejected(tmp_path):
    root = copy_evidence(tmp_path)
    rewrite(root / "r9_arm_C.json", lambda d: d["cases"]["G02_moderate_guidance"]["raw_job"]["receipts"][0].__setitem__("prompt_tokens", 999999))
    with pytest.raises(AssertionError):
        main(root, write=False)


def test_corrupt_physical_measurement_is_rejected(tmp_path):
    root = copy_evidence(tmp_path)
    rewrite(root / "r9_arm_D.json", lambda d: d["cases"]["G04_petg_material"]["raw_job"]["repair_attempt"]["candidate"]["joint_corners"][0]["result"].__setitem__("absolute_drift_mm", 999))
    with pytest.raises(AssertionError):
        main(root, write=False)


def test_corrupt_frozen_constraint_is_rejected(tmp_path):
    root = copy_evidence(tmp_path)
    rewrite(root / "r9_frozen_tasks.json", lambda d: d["cases"][0]["constraints"].__setitem__("force_n", 9))
    with pytest.raises(AssertionError):
        main(root, write=False)

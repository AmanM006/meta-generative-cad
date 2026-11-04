"""Offline state-machine checks; no paid model call and no solver shortcut in production."""
import asyncio
import json

import pytest
from fastapi import HTTPException

import live_engineering_service as live
from run_clarification_20 import deterministic


REQUEST = "Design a PP guide for a 6 N load, 1.5 mm stroke, 75 x 50 mm package, drift under 0.03 mm, stress under 25 MPa."
CODE = "test-only-code"


@pytest.fixture
def controlled(monkeypatch):
    test_dir = live.ROOT / ".runtime_live"
    test_dir.mkdir(exist_ok=True)
    test_budget = test_dir / "test_budget.json"
    if test_budget.exists():
        test_budget.unlink()
    monkeypatch.setenv("MODEL_API_KEY", "dummy-test-token")
    monkeypatch.setenv("LIVE_DEMO_ACCESS_CODE", CODE)
    monkeypatch.setattr(live, "PRIVATE", test_dir)
    monkeypatch.setattr(live, "BUDGET_FILE", test_budget)
    monkeypatch.setattr(live, "JOBS", {})
    monkeypatch.setattr(live, "evaluate", lambda proposal, task, mesh_density: {
        "feasible": mesh_density == 16 or proposal["connections"][0]["thickness"] >= .0009,
        "gates": {"stroke": True, "drift": True}, "stroke_mm": 1.7,
        "absolute_drift_mm": .02, "stress_mpa": 18.0,
    })
    receipt = {"model": "test-muse", "request_id": "test-id", "request_sha256": "a",
               "response_sha256": "b", "estimated_cost_usd": .0001}
    monkeypatch.setattr(live, "call_muse_live", lambda text: (json.dumps(deterministic(REQUEST)), receipt))
    yield test_dir
    if test_budget.exists():
        test_budget.unlink()


async def finish(job_id):
    for _ in range(200):
        job = live.JOBS[job_id]
        if job["status"] in {"completed", "unresolved", "error", "abstained"}:
            return job
        await asyncio.sleep(.01)
    raise AssertionError("job failed to finish")


def test_live_model_receipt_and_solver_decision(controlled):
    async def run():
        response = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        job = await finish(response["id"])
        assert job["status"] == "completed"
        assert job["selected_mm"] == 1.0
        assert len(job["receipts"]) == 1
        assert live.budget()["reserved_calls"] == 1
        assert job["trials"][0]["fine"] is not None
        assert job["trials"][-1]["joint_corners"]
        assert "receipts" not in live.public(job)
    asyncio.run(run())


def test_independent_gate_blocks_unsupported_before_model(controlled):
    async def run():
        with pytest.raises(HTTPException) as error:
            await live.start(live.StartRequest(request_text=REQUEST + " Include fatigue proof.", access_code=CODE))
        assert error.value.status_code == 422
        assert live.budget()["reserved_calls"] == 0
    asyncio.run(run())


def test_auth_and_ungrounded_model_value(controlled):
    with pytest.raises(HTTPException) as error:
        live.authorize("bad-code")
    assert error.value.status_code == 403
    candidate = deterministic(REQUEST)
    candidate["constraints"]["force_n"] = 9
    with pytest.raises(ValueError, match="unit-backed"):
        live.compiled_from_candidate(candidate, REQUEST)

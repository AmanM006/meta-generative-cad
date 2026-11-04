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
    monkeypatch.setattr(live, "START_TIMES", [])
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
        assert job["status"] == "completed", job.get("error")
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


def test_model_failure_does_not_expose_exception_or_key(controlled, monkeypatch):
    monkeypatch.setattr(live, "call_muse_live", lambda text: (_ for _ in ()).throw(RuntimeError("sk-private-test-key")))
    async def run():
        response = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        job = await finish(response["id"])
        assert job["status"] == "error"
        assert "sk-private-test-key" not in json.dumps(live.public(job))
        assert live.budget()["reserved_calls"] == 1
    asyncio.run(run())


def test_model_budget_stops_before_api_call(controlled, monkeypatch):
    live.persist_budget({"reserved_calls": live.MAX_MODEL_CALLS, "estimated_spend_usd": 0})
    called = []
    monkeypatch.setattr(live, "call_muse_live", lambda text: called.append(text))
    async def run():
        response = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        job = await finish(response["id"])
        assert job["status"] == "error"
        assert called == []
        assert live.budget()["reserved_calls"] == live.MAX_MODEL_CALLS
    asyncio.run(run())


def test_job_token_controls_status_and_is_never_returned_again(controlled):
    async def run():
        started = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        ident, token = started["id"], started["job_token"]
        assert "job_token_sha256" not in started
        with pytest.raises(HTTPException) as denied:
            await live.status(ident, live.StatusRequest(access_code=CODE, job_token="x" * 40))
        assert denied.value.status_code == 403
        visible = await live.status(ident, live.StatusRequest(access_code=CODE, job_token=token))
        assert "job_token" not in visible and "job_token_sha256" not in visible
        assert token not in (controlled / (ident + ".json")).read_text()
    asyncio.run(run())


def test_rate_limit_and_active_job_limit(controlled):
    async def run():
        one = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        two = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        with pytest.raises(HTTPException) as busy:
            await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        assert busy.value.status_code == 429
        live.JOBS[one["id"]]["status"] = "completed"
        live.JOBS[two["id"]]["status"] = "completed"
        live.START_TIMES[:] = [live.time.monotonic()] * live.MAX_STARTS_PER_MINUTE
        with pytest.raises(HTTPException) as limited:
            await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE))
        assert limited.value.status_code == 429
    asyncio.run(run())


def test_idle_clarification_releases_capacity(controlled):
    job = {"id": "expired-test", "status": "needs_clarification", "events": [],
           "last_action_epoch": live.time.time() - live.CLARIFICATION_TTL_SECONDS - 1}
    live.JOBS[job["id"]] = job
    live.expire_idle_clarifications()
    assert job["status"] == "expired"


def test_scaled_geometry_uses_actual_package_and_petg_material(controlled):
    source = json.loads(live.SOURCE.read_text())
    base = source["results"]["C01/muse_cold"]["physical_screen"]["physics"]["proposal"]
    scaled = live.proposal_for_envelope(base, [60, 40])
    assert max(anchor[0] for anchor in scaled["anchors"]) == .06
    assert scaled["stages"][0]["height"] == pytest.approx(base["stages"][0]["height"] * .8)
    spec = {"constraints": {"material": "petg", "force_n": 2.0, "stroke_min_mm": .6,
                            "envelope_mm": [60, 40], "drift_max_mm": .03, "stress_max_mpa": 30},
            "measured_E_gpa": 2.5}
    task = live.task_for(spec)
    assert task["envelope_m"] == [.06, .04]
    assert task["material_properties"]["E_pa"] == 2.5e9


def test_explicit_unsupported_package_rejected_before_model(controlled):
    async def run():
        with pytest.raises(HTTPException) as rejected:
            await live.start(live.StartRequest(
                request_text="Design a PP guide for 6 N load, 1.2 mm stroke in a 40 x 30 mm package.",
                access_code=CODE))
        assert rejected.value.status_code == 422
        assert live.budget()["reserved_calls"] == 0
    asyncio.run(run())


def test_muse_repair_is_compiled_measured_and_attributed(controlled, monkeypatch):
    hypothesis = {"diagnosis": "The thinner corner bends asymmetrically and exceeds the lateral drift limit.",
                  "failed_gate": "absolute_drift", "action": "uniform_plus_0p1",
                  "predicted_stroke_direction": "unchanged", "predicted_drift_direction": "unchanged"}
    receipt = {"model": "test-muse", "request_id": "repair-id", "request_sha256": "c",
               "response_sha256": "d", "estimated_cost_usd": .0001}
    monkeypatch.setattr(live, "call_muse_repair_live", lambda prompt: (json.dumps(hypothesis), receipt))
    # The fake failed corner must name the gate Muse is asked to diagnose.
    def fake_evaluate(proposal, task, mesh_density):
        passed = mesh_density == 16 or proposal["connections"][0]["thickness"] >= .0009
        return {"feasible": passed, "gates": {"absolute_drift": passed},
                "stroke_mm": 1.7, "absolute_drift_mm": .02, "stress_mpa": 18.0}
    monkeypatch.setattr(live, "evaluate", fake_evaluate)
    async def run():
        started = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE,
                                                     repair_mode="muse_directed"))
        job = await finish(started["id"])
        assert job["status"] == "completed", job.get("error")
        assert job["selection_source"] == "muse_directed_proposal_independently_verified"
        assert job["repair_attempt"]["verdict"] == "robust_beam_pass"
        assert len(job["receipts"]) == 2
    asyncio.run(run())


def test_invalid_muse_repair_counts_failure_and_uses_labeled_fallback(controlled, monkeypatch):
    receipt = {"model": "test-muse", "request_id": "repair-bad-id", "request_sha256": "c",
               "response_sha256": "d", "estimated_cost_usd": .0001}
    monkeypatch.setattr(live, "call_muse_repair_live", lambda prompt: ('{"action":"invented"}', receipt))
    async def run():
        started = await live.start(live.StartRequest(request_text=REQUEST, access_code=CODE,
                                                     repair_mode="muse_directed"))
        job = await finish(started["id"])
        assert job["status"] == "completed", job.get("error")
        assert job["repair_attempt"]["verdict"].startswith("invalid_or_failed_repair_")
        assert job["selection_source"] == "deterministic_fallback_after_muse"
        assert len(job["receipts"]) == 2
    asyncio.run(run())

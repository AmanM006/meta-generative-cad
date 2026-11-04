"""Safety and provenance regression checks for the hosted Intent Lab API."""
from fastapi.testclient import TestClient

from server import app


def interpret(client, text):
    response = client.post("/api/intent/interpret", json={"mode": "deterministic", "request_text": text})
    assert response.status_code == 200, response.text
    return response.json()


def main():
    client = TestClient(app)
    contradictory = interpret(client, "A PP stage under 6 N needs 1.2 mm stroke in 75 x 50 mm; drift below 0.01 mm and at least 0.05 mm.")
    assert contradictory["clarification"]["action"] == "abstain" and contradictory["physics"] is None
    unsupported = interpret(client, "A PP stage under 6 N needs 1.2 mm stroke in 75 x 50 mm and out-of-plane torsion certification.")
    assert unsupported["clarification"]["action"] == "abstain" and unsupported["physics"] is None
    vague = interpret(client, "Use recycled PP under 6 N for 1.2 mm stroke in 75 x 50 mm; elastic modulus unknown.")
    assert vague["clarification"]["field"] == "material_properties"
    resolved = interpret(client, "Use recycled PP under 6 N for 1.2 mm stroke in 75 x 50 mm; elastic modulus unknown. measured modulus 1.4 GPa.")
    assert resolved["clarification"]["action"] == "proceed"
    assert resolved["interpretation"]["material_properties"]["measured_E_gpa"] == 1.4
    recorded = client.post("/api/intent/interpret", json={"mode": "recorded_clarification", "example_id": "Q12"}).json()
    assert not recorded["reference_score"]["full_case"] and recorded["physics"] is None
    live_replay = client.post("/api/intent/interpret", json={"mode": "recorded_local_live", "example_id": "L01"}).json()
    assert live_replay["execution_mode"] == "RECORDED_LOCAL_LIVE_MUSE_AND_FEA"
    assert live_replay["initial_joint_failure"]["absolute_drift_mm"] > live_replay["initial_joint_failure"]["drift_limit_mm"]
    assert live_replay["robust_search"]["fine_robust"] and live_replay["physics"]["feasible"]
    print("CLARIFICATION_API_PASS 6 safety/provenance scenarios")


if __name__ == "__main__":
    main()

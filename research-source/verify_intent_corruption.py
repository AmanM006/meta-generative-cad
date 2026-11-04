"""Prove the intent auditor rejects six independent evidence corruptions."""
import copy
import json
import uuid
from pathlib import Path

import audit_engineering_intent as auditor

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "fresh_evidence/intent_spec_confirmatory_frozen.json").read_text())
LEDGER = json.loads((ROOT / "fresh_evidence/intent_spec_confirmatory_results.json").read_text())


def main():
    scratch = ROOT / "fresh_evidence" / ("_intent_audit_" + uuid.uuid4().hex)
    data_dir = scratch / "fresh_evidence"
    data_dir.mkdir(parents=True)
    original_root = auditor.ROOT
    auditor.ROOT = scratch
    def frozen_units(s, l): s["held_out"][0]["reference"]["constraints"]["force_n"] = 6000
    def response_hash(s, l): l["receipts"][0]["response"] += "tampered"
    def stored_score(s, l): l["results"]["C01/muse_cold"]["score"]["complete_correct"] = False
    def stress_limit(s, l): l["results"]["C01/muse_cold"]["physical_screen"]["task"]["stress_max_mpa"] = 200
    def drift_limit(s, l): l["results"]["C01/muse_cold"]["physical_screen"]["task"]["drift_max_mm"] = .3
    def model_output(s, l): l["results"]["C01/muse_cold"]["candidate"]["constraints"]["force_n"] = 6000
    def stored_verdict(s, l): l["results"]["C01/muse_cold"]["physical_screen"]["physics"]["feasible"] = True
    mutations = {"frozen_units": frozen_units, "response_hash": response_hash,
                 "stored_score": stored_score, "stress_limit": stress_limit,
                 "drift_limit": drift_limit, "model_output": model_output,
                 "stored_verdict": stored_verdict}
    try:
        for name, mutate in mutations.items():
            spec, ledger = copy.deepcopy(SPEC), copy.deepcopy(LEDGER)
            mutate(spec, ledger)
            (data_dir / "intent_spec_confirmatory_frozen.json").write_text(json.dumps(spec))
            (data_dir / "intent_spec_confirmatory_results.json").write_text(json.dumps(ledger))
            try:
                auditor.audit(physics=False)
            except AssertionError:
                print(name, "REJECTED")
            else:
                raise AssertionError(f"Corruption accepted: {name}")
    finally:
        auditor.ROOT = original_root
        for file in data_dir.iterdir(): file.unlink()
        data_dir.rmdir()
        scratch.rmdir()


if __name__ == "__main__":
    main()

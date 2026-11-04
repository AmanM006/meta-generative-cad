"""Check the independent audit rejects altered tasks, receipts, scores and costs."""
import copy
import json

from audit_clarification_20 import FROZEN, LEDGER, audit


def main():
    frozen = json.loads(FROZEN.read_text())
    ledger = json.loads(LEDGER.read_text())
    mutations = (
        ("frozen_request", "frozen", lambda d: d["cases"][0].__setitem__("request", "altered request")),
        ("receipt_response", "ledger", lambda d: d["receipts"][0].__setitem__("response", "{}")),
        ("receipt_request", "ledger", lambda d: d["receipts"][0]["request"]["messages"][0].__setitem__("content", "altered")),
        ("stored_score", "ledger", lambda d: d["results"]["Q01/muse_cold"]["score"].__setitem__("full_case", False)),
        ("question_field", "ledger", lambda d: d["results"]["Q02/muse_cold"]["candidate"].__setitem__("question_field", "material")),
        ("total_cost", "ledger", lambda d: d.__setitem__("new_estimated_cost_usd", 0)),
    )
    for name, which, mutate in mutations:
        changed_frozen, changed_ledger = copy.deepcopy(frozen), copy.deepcopy(ledger)
        mutate(changed_frozen if which == "frozen" else changed_ledger)
        try:
            audit(frozen_data=changed_frozen, ledger_data=changed_ledger)
        except (AssertionError, ValueError, KeyError, TypeError):
            print(name, "REJECTED")
        else:
            raise AssertionError("Audit accepted corruption: " + name)


if __name__ == "__main__":
    main()

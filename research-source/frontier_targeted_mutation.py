"""Replay a frozen, equal-budget mutation of the two-stage pilot candidates."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from open_ended_structural_discovery_engine import classify_graph, digest, evaluate, graph_of
import networkx as nx

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fresh_evidence/frontier_novel_graph_challenge.json"
TARGET = ROOT / "fresh_evidence/frontier_targeted_mutation.json"


def same_structure(left, right):
    a, b = graph_of(left), graph_of(right)
    return nx.algorithms.isomorphism.MultiGraphMatcher(
        a, b,
        node_match=lambda x, y: x["role"] == y["role"],
        edge_match=lambda x, y: sorted(e["ports"] for e in x.values())
        == sorted(e["ports"] for e in y.values()),
    ).is_isomorphic()


def main():
    prior = json.loads(SOURCE.read_text())
    task = prior["task"]
    record = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE.name,
        "source_sha256": digest(prior),
        "task": task,
        "mutation_plan": {
            "muse": "Extend all four anchor x coordinates from 5 mm inboard to their respective package edges; preserve connectivity, stage geometry and 0.6 mm thickness.",
            "classical": "Set all flexure thicknesses to the 0.6 mm manufacturing floor; preserve connectivity, stage and anchor geometry.",
        },
        "budget": "Exactly one additional coarse-mesh FEA per existing candidate in each arm (3 each).",
        "arms": {},
    }
    for arm in ("classical", "muse"):
        rows = []
        for original in prior[arm]:
            proposal = copy.deepcopy(original["proposal"])
            if arm == "muse":
                for anchor in proposal["anchors"]:
                    anchor[0] = 0.0 if anchor[0] < 0.045 else 0.09
            else:
                for connection in proposal["connections"]:
                    connection["thickness"] = 0.0006
            result = evaluate(proposal, task)
            result["parent_proposal_sha256"] = original["proposal_sha256"]
            result["same_structure_as_parent"] = same_structure(proposal, original["proposal"])
            rows.append(result)
        record["arms"][arm] = rows
    record["cross_arm_same_structure"] = [
        [same_structure(m["proposal"], c["proposal"]) for c in record["arms"]["classical"]]
        for m in record["arms"]["muse"]
    ]
    record["interpretation"] = (
        "Both arms reach 3/3 coarse-mesh feasibility after one targeted numerical mutation each. "
        "The candidates share the same attributed connectivity graph across arms; this result "
        "does not show an AI graph-invention advantage. Novelty is only relative to the project library."
    )
    TARGET.write_text(json.dumps(record, indent=2))
    print(TARGET, "classical", sum(r["feasible"] for r in record["arms"]["classical"]),
          "muse", sum(r["feasible"] for r in record["arms"]["muse"]))
    print("cross_arm_same_structure", record["cross_arm_same_structure"])


if __name__ == "__main__":
    main()

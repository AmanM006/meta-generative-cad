"""Fail-closed graph proposal compiler and matched pilot evaluation."""
import hashlib
import json
import math
import time
from pathlib import Path

import networkx as nx
import numpy as np

from compliant_solver import CompliantFrameSolver
from engineering_runtime.hardened_compiler import HardenedCompactCompiler

ROOT = Path(__file__).resolve().parent
SCHEMA = json.loads((ROOT / "FRONTIER_TYPED_GRAPH_SCHEMA.json").read_text())
MATERIAL = SCHEMA["material"]

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate_proposal(proposal, min_thickness=0.0006):
    if not isinstance(proposal, dict):
        raise ValueError("Proposal must be an object")
    for key in SCHEMA["required_proposal_fields"]:
        if key not in proposal:
            raise ValueError(f"Missing {key}")
    if not (2 <= len(proposal["anchors"]) <= 8 and 1 <= len(proposal["stages"]) <= 4):
        raise ValueError("Anchor or stage count outside pilot grammar")
    if not (2 <= len(proposal["connections"]) <= 16):
        raise ValueError("Connection count outside pilot grammar")
    for anchor in proposal["anchors"]:
        if len(anchor) != 2 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in anchor):
            raise ValueError("Invalid anchor coordinate")
    for stage in proposal["stages"]:
        if stage.get("type") != "rigid_stage" or len(stage.get("center", [])) != 2:
            raise ValueError("Invalid stage type or center")
        if not (0.005 <= stage.get("height", 0) <= 0.051):
            raise ValueError("Invalid stage height")
    for edge in proposal["connections"]:
        if edge.get("type") != "flexure_beam":
            raise ValueError("Only flexure beams are allowed")
        for side in ("from", "to"):
            kind = edge.get(f"{side}_type")
            index = edge.get(f"{side}_index")
            port = edge.get(f"{side}_port")
            if kind not in ("anchor", "stage") or not isinstance(index, int) or index < 0:
                raise ValueError("Invalid endpoint type or index")
            if index >= len(proposal["anchors" if kind == "anchor" else "stages"]):
                raise ValueError("Endpoint index out of range")
            allowed = ("center",) if kind == "anchor" else ("top", "bot", "center", *proposal["stages"][index].get("ports", {}).keys())
            if port not in allowed:
                raise ValueError("Invalid port")
        if not (min_thickness <= edge.get("thickness", 0) <= 0.0025):
            raise ValueError("Manufacturing floor or thickness limit violated")
    if not isinstance(proposal["output_stage"], int) or not 0 <= proposal["output_stage"] < len(proposal["stages"]):
        raise ValueError("Invalid output stage")
    spec = {k: proposal[k] for k in SCHEMA["required_proposal_fields"]}
    spec["stages"] = [{k: v for k, v in s.items() if k != "type"} for s in spec["stages"]]
    spec["connections"] = [{k: v for k, v in e.items() if k != "type"} for e in spec["connections"]]
    return spec

def graph_of(proposal):
    graph = nx.MultiGraph()
    for i in range(len(proposal["anchors"])):
        graph.add_node(("anchor", i), role="ground")
    for i in range(len(proposal["stages"])):
        graph.add_node(("stage", i), role="output" if i == proposal["output_stage"] else "stage")
    for e in proposal["connections"]:
        graph.add_edge((e["from_type"], e["from_index"]), (e["to_type"], e["to_index"]),
                       ports=tuple(sorted((e["from_port"], e["to_port"]))))
    return graph

def classify_graph(proposal, library):
    graph = graph_of(proposal)
    for name, exemplar in library.items():
        base = graph_of(exemplar)
        matcher = nx.algorithms.isomorphism.MultiGraphMatcher(
            graph, base,
            node_match=lambda x, y: x["role"] == y["role"],
            edge_match=lambda x, y: sorted(e["ports"] for e in x.values()) == sorted(e["ports"] for e in y.values()))
        if matcher.is_isomorphic():
            return {"class": "existing_template" if digest(proposal) == digest(exemplar) else "parameter_variation",
                    "matched_library_entry": name, "literature_novelty": "NOT_ASSESSED"}
    return {"class": "new_graph_relative_to_project_library", "matched_library_entry": None,
            "literature_novelty": "NOT_ASSESSED"}

def evaluate(proposal, task, mesh_density=4):
    t0 = time.perf_counter()
    record = {"proposal": proposal, "proposal_sha256": digest(proposal), "task_sha256": digest(task),
              "mesh_elements_per_beam": mesh_density}
    try:
        envelope = task.get("envelope_m", SCHEMA["envelope_m"])
        if len(envelope) != 2 or any(not isinstance(v, (int, float)) or v <= 0 for v in envelope):
            raise ValueError("Invalid task envelope")
        material = task.get("material_properties", MATERIAL)
        if any(not isinstance(material.get(k), (int, float)) or material[k] <= 0
               for k in ("E_pa", "yield_strength_pa", "depth_m")):
            raise ValueError("Invalid material properties")
        spec = validate_proposal(proposal, task.get("min_flexure_thickness_m", 0.0006))
        mesh = HardenedCompactCompiler(max_x=envelope[0], max_y=envelope[1]).compile(spec, n_elem_per_beam=mesh_density)
        nodes, elements, widths = mesh["nodes"], mesh["elements"], mesh["widths"]
        boundaries = [3*g+d for g in mesh["ground_nodes"] for d in range(3)]
        force = np.zeros(3*len(nodes))
        output_dof = 3*mesh["output_node"]+1
        force[output_dof] = task["force_n"]
        solver = CompliantFrameSolver(E=material["E_pa"], yield_strength=material["yield_strength_pa"],
                                      depth=material["depth_m"])
        solution = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, boundaries, force)
        u = solution["displacements"]
        dy, dx = float(u[output_dof]*1000), float(abs(u[output_dof-1])*1000)
        stress = float(solution["max_stress_MPa"])
        deformed = nodes + np.column_stack((u[0::3], u[1::3]))
        in_envelope = bool(np.all(deformed[:, 0] >= -1e-6) and np.all(deformed[:, 0] <= envelope[0]+1e-6)
                           and np.all(deformed[:, 1] >= -1e-6) and np.all(deformed[:, 1] <= envelope[1]+1e-6))
        _, tangent, _ = solver.compute_internal_forces_and_tangent(nodes, elements, widths, u)
        free = np.array([i for i in range(len(u)) if i not in set(boundaries)], dtype=int)
        min_eig = float(np.linalg.eigvalsh(tangent[np.ix_(free, free)])[0])
        gates = {"stroke": dy >= task["stroke_min_mm"], "absolute_drift": dx <= task["drift_max_mm"],
                 "stress": stress <= task["stress_max_mpa"], "tangent_stability": min_eig > 0,
                 "deformed_envelope": in_envelope}
        record.update(status="evaluated", feasible=all(gates.values()), gates=gates,
                      stroke_mm=dy, absolute_drift_mm=dx, stress_mpa=stress,
                      tangent_min_eigenvalue=min_eig, node_count=len(nodes), element_count=len(elements),
                      compiler_spec=spec)
    except Exception as exc:
        record.update(status="rejected", feasible=False, reason=f"{type(exc).__name__}: {exc}")
    record["duration_s"] = time.perf_counter()-t0
    return record

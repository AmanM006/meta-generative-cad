"""Compact Structural Architecture Compiler for Compliant Mechanisms.

Translates high-level structural primitives into connected 2D beam FEA meshes.
Supported Primitives:
- anchors: list of ground connection points (e.g. [[0, 0], [0, 0.030]])
- stages: list of rigid or flexible stages with specific positions and sizes
- flexure_groups: list of flexible beam connections between nodes or stages:
    * count: number of parallel flexures in group (e.g. 1, 2, 4)
    * length: span of flexure
    * orientation_deg: angle of flexure (0 = horizontal along X, 90 = vertical along Y)
    * thickness: beam thickness in meters
    * connection_from: anchor_index or stage_index
    * connection_to: stage_index
- symmetry: "NONE", "MIRROR_Y", "MIRROR_X", "CENTRAL"
- output_stage: index of the guided stage where actuation force F_y is applied.

Rejection Rules (Strict Verification):
1. Must have at least 1 grounded anchor.
2. Must have a valid output stage.
3. Graph must be connected (no floating or disconnected elements).
4. Beam thicknesses and lengths must be within physical fabrication bounds:
   - length in [0.005, 0.090] m
   - thickness in [0.0004, 0.006] m
5. Mechanism must fit within bounding box: X in [0, 0.095] m, Y in [0, 0.060] m.
"""

import numpy as np

class CompactArchitectureCompiler:
    def __init__(self, bounds_x=(0.0, 0.095), bounds_y=(0.0, 0.060)):
        self.bounds_x = bounds_x
        self.bounds_y = bounds_y

    def compile(self, spec, n_elem_per_beam=6):
        """
        Takes spec dict, validates, and returns:
            nodes (N, 2), elements (M, 2), widths (M,), ground_nodes (list), output_node (int)
        Raises ValueError if invalid or disconnected.
        """
        # Basic field checks
        required_keys = ["anchors", "stages", "connections", "output_stage"]
        for k in required_keys:
            if k not in spec:
                raise ValueError(f"Missing required key '{k}' in design spec.")

        anchors = spec["anchors"]
        stages = spec["stages"]
        connections = spec["connections"]
        output_stage_idx = spec["output_stage"]

        if len(anchors) == 0:
            raise ValueError("Mechanism has no grounded anchors.")
        if output_stage_idx < 0 or output_stage_idx >= len(stages):
            raise ValueError(f"Invalid output_stage index {output_stage_idx}.")

        nodes = []
        elements = []
        widths = []
        ground_node_indices = []

        # 1. Instantiate Anchor Nodes
        anchor_node_map = {}
        for a_idx, pt in enumerate(anchors):
            x, y = pt[0], pt[1]
            if not (self.bounds_x[0] <= x <= self.bounds_x[1] and self.bounds_y[0] <= y <= self.bounds_y[1]):
                raise ValueError(f"Anchor {a_idx} at ({x}, {y}) exceeds bounding box.")
            node_idx = len(nodes)
            nodes.append([x, y])
            ground_node_indices.append(node_idx)
            anchor_node_map[a_idx] = node_idx

        # 2. Instantiate Stage Nodes
        # Each stage has a center (x, y) and height H_stage
        stage_node_map = {}
        for s_idx, st in enumerate(stages):
            cx, cy = st["center"]
            h_st = st.get("height", 0.010)
            is_rigid = st.get("is_rigid", True)
            t_rigid = 0.008 if is_rigid else st.get("thickness", 0.002)

            if not (self.bounds_x[0] <= cx <= self.bounds_x[1] and self.bounds_y[0] <= cy <= self.bounds_y[1]):
                raise ValueError(f"Stage {s_idx} center ({cx}, {cy}) exceeds bounding box.")

            # A stage consists of top, mid, bot nodes connected rigidly
            n_mid = len(nodes)
            nodes.append([cx, cy])
            n_top = len(nodes)
            nodes.append([cx, cy + h_st / 2.0])
            n_bot = len(nodes)
            nodes.append([cx, cy - h_st / 2.0])

            # Connect stage rigidly
            elements.append([n_bot, n_mid])
            widths.append(t_rigid)
            elements.append([n_mid, n_top])
            widths.append(t_rigid)

            stage_node_map[s_idx] = {"mid": n_mid, "top": n_top, "bot": n_bot}

        # 3. Instantiate Connections (Flexures)
        for c_idx, conn in enumerate(connections):
            from_type = conn.get("from_type", "anchor") # 'anchor' or 'stage'
            from_idx = conn["from_index"]
            from_port = conn.get("from_port", "center") # 'center', 'top', 'bot'

            to_type = conn.get("to_type", "stage")
            to_idx = conn["to_index"]
            to_port = conn.get("to_port", "center")

            thickness = conn.get("thickness", 0.001)
            if not (0.0004 <= thickness <= 0.006):
                raise ValueError(f"Connection {c_idx} thickness {thickness} out of bounds [0.0004, 0.006].")

            # Resolve start point
            if from_type == "anchor":
                p_start_idx = anchor_node_map[from_idx]
                p_start = nodes[p_start_idx]
            else:
                port_key = "mid" if from_port == "center" else from_port
                p_start_idx = stage_node_map[from_idx][port_key]
                p_start = nodes[p_start_idx]

            # Resolve end point
            if to_type == "anchor":
                p_end_idx = anchor_node_map[to_idx]
                p_end = nodes[p_end_idx]
            else:
                port_key = "mid" if to_port == "center" else to_port
                p_end_idx = stage_node_map[to_idx][port_key]
                p_end = nodes[p_end_idx]

            dx = p_end[0] - p_start[0]
            dy = p_end[1] - p_start[1]
            L = np.sqrt(dx**2 + dy**2)
            if L < 0.005 or L > 0.090:
                raise ValueError(f"Connection {c_idx} length {L:.4f}m out of bounds [0.005, 0.090]m.")

            # Subdivide flexure beam into n_elem_per_beam
            internal_nodes = []
            for seg in range(1, n_elem_per_beam):
                frac = seg / float(n_elem_per_beam)
                px = p_start[0] + frac * dx
                py = p_start[1] + frac * dy
                internal_nodes.append(len(nodes))
                nodes.append([px, py])

            # Connect chain
            chain = [p_start_idx] + internal_nodes + [p_end_idx]
            for i in range(len(chain) - 1):
                elements.append([chain[i], chain[i + 1]])
                widths.append(thickness)

        nodes = np.array(nodes)
        elements = np.array(elements)
        widths = np.array(widths)

        # 4. Graph Connectivity Verification (Union-Find)
        num_nodes = len(nodes)
        parent = list(range(num_nodes))
        def find(i):
            path = []
            while parent[i] != i:
                path.append(i)
                i = parent[i]
            for node in path:
                parent[node] = i
            return i

        for u, v in elements:
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv

        # Ensure all nodes are connected to at least one ground anchor
        ground_roots = {find(g) for g in ground_node_indices}
        output_mid = stage_node_map[output_stage_idx]["mid"]
        output_root = find(output_mid)

        if output_root not in ground_roots:
            raise ValueError("Output stage is completely disconnected from ground anchors!")

        for n_i in range(num_nodes):
            if find(n_i) != output_root:
                raise ValueError(f"Disconnected or floating node detected at index {n_i}.")

        return {
            "nodes": nodes,
            "elements": elements,
            "widths": widths,
            "ground_nodes": ground_node_indices,
            "output_node": output_mid,
            "stage_mid_nodes": [stage_node_map[s]["mid"] for s in range(len(stages))]
        }

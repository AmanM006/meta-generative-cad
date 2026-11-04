"""
Compositional Topology Synthesizer v2.
Conforms strictly to HardenedCompactCompiler schema:
- anchors: list of [x, y] coordinates
- stages: list of dicts with center, height, thickness, is_rigid, ports {'top', 'bot', ...}
- connections: list of dicts with from_type, from_index, from_port, to_type, to_index, to_port, thickness
- output_stage: int index of the output shuttle
"""

import copy
import numpy as np

class CompositionalTopologySynthesizer:
    def __init__(self, env_x, env_y):
        self.env_x = env_x
        self.env_y = env_y
        self.margin = 0.005

    def synthesize_multistage_shuttle_tree(self, num_intermediate_shuttles=2, taper_ratio=0.75):
        """
        Synthesizes a novel multi-stage serial-parallel compliance tree:
        Left Anchors -> Intermediate Shuttles -> Central Guided Output Stage
        Absorbs axial chord tension via independent kinematic stages while multiplying transverse stroke.
        """
        anchors = [
            [self.margin, self.env_y - self.margin], # top left (0)
            [self.margin, self.margin]               # bot left (1)
        ]
        
        stages = []
        x_positions = np.linspace(self.margin + 0.015, self.env_x - self.margin - 0.010, num_intermediate_shuttles + 1)
        
        # Intermediate shuttles
        for s_idx in range(num_intermediate_shuttles):
            xs = float(x_positions[s_idx])
            ys = float(self.env_y / 2.0)
            h_stage = float(self.env_y - 2 * self.margin)
            stages.append({
                "center": [xs, ys],
                "height": h_stage,
                "thickness": 0.003,
                "is_rigid": True,
                "ports": {
                    "top": [xs, ys + h_stage / 2.0],
                    "bot": [xs, ys - h_stage / 2.0],
                    "center": [xs, ys]
                }
            })

        # Final Output Shuttle
        out_idx = num_intermediate_shuttles
        xs_out = float(x_positions[-1])
        ys_out = float(self.env_y / 2.0)
        h_out = float(self.env_y * 0.60)
        stages.append({
            "center": [xs_out, ys_out],
            "height": h_out,
            "thickness": 0.003,
            "is_rigid": True,
            "ports": {
                "top": [xs_out, ys_out + h_out / 2.0],
                "bot": [xs_out, ys_out - h_out / 2.0],
                "center": [xs_out, ys_out]
            }
        })

        connections = [
            # Connect Ground Anchors to First Shuttle
            {"from_type": "anchor", "from_index": 0, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "top", "thickness": 0.00095},
            {"from_type": "anchor", "from_index": 1, "from_port": "center", "to_type": "stage", "to_index": 0, "to_port": "bot", "thickness": 0.00095}
        ]

        # Connect successive shuttles
        for s in range(num_intermediate_shuttles):
            next_stage = s + 1
            connections.append({
                "from_type": "stage", "from_index": s, "from_port": "top",
                "to_type": "stage", "to_index": next_stage, "to_port": "top",
                "thickness": 0.00095
            })
            connections.append({
                "from_type": "stage", "from_index": s, "from_port": "bot",
                "to_type": "stage", "to_index": next_stage, "to_port": "bot",
                "thickness": 0.00095
            })

        spec = {
            "id": f"NOVEL_COMPOSITIONAL_SHUTTLE_{num_intermediate_shuttles}STAGE_TAPER{int(taper_ratio*100)}",
            "class": "compositional_shuttle_tree",
            "num_shuttles": num_intermediate_shuttles,
            "taper_ratio": taper_ratio,
            "output_stage": out_idx,
            "anchors": anchors,
            "stages": stages,
            "connections": connections
        }
        return spec["id"], spec

print("Compositional Topology Synthesizer v2 defined successfully!")

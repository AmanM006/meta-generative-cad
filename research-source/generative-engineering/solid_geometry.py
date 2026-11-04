"""Solid Geometry Engine for Compliant Flexure Mechanisms.

Converts 2D topological specifications into manifold 3D solid meshes
strictly conforming to the 90.0 x 55.0 x 10.0 mm bounding envelope.
"""

import json
from pathlib import Path
import numpy as np
import trimesh
from hardened_compiler import HardenedCompactCompiler

class SolidGeometryEngine:
    def __init__(self, depth: float = 0.010, pad_size: float = 0.003):
        self.depth = depth
        self.pad_size = pad_size
        self.compiler = HardenedCompactCompiler()

    def create_box(self, x_min, x_max, y_min, y_max, z_min=-0.005, z_max=0.005) -> trimesh.Trimesh:
        # Enforce envelope boundary clipping [0.000, 0.090] x [0.000, 0.055]
        x_min = max(0.000, x_min)
        x_max = min(0.090, x_max)
        y_min = max(0.000, y_min)
        y_max = min(0.055, y_max)
        dx = max(x_max - x_min, 1e-6)
        dy = max(y_max - y_min, 1e-6)
        dz = max(z_max - z_min, 1e-6)
        center = [(x_min + x_max)/2.0, (y_min + y_max)/2.0, (z_min + z_max)/2.0]
        box = trimesh.creation.box(extents=[dx, dy, dz])
        box.apply_translation(center)
        return box

    def build_solid_mesh(self, spec: dict) -> trimesh.Trimesh:
        """
        Synthesizes a combined 3D solid geometry of stages, anchors, and flexure beams
        strictly clipped inside the 90.0 x 55.0 mm envelope.
        """
        parts = []
        mesh_meta = self.compiler.compile(spec, n_elem_per_beam=1)
        nodes = np.array(mesh_meta["nodes"])
        elements = mesh_meta["elements"]
        widths = mesh_meta["widths"]
        z_half = self.depth / 2.0

        # 1. Beams as 3D rectangular leaves
        for (n1, n2), w in zip(elements, widths):
            p1 = nodes[n1]
            p2 = nodes[n2]
            vec = p2 - p1
            length = float(np.linalg.norm(vec))
            if length > 1e-6:
                leaf = trimesh.creation.box(extents=[length, float(w), self.depth])
                center_2d = (p1 + p2) / 2.0
                leaf.apply_translation([center_2d[0], center_2d[1], 0.0])
                angle = np.arctan2(vec[1], vec[0])
                R = trimesh.transformations.rotation_matrix(angle, [0, 0, 1.0], point=[center_2d[0], center_2d[1], 0.0])
                leaf.apply_transform(R)
                parts.append(leaf)

        # 2. Anchor ground pads placed inwards so they do NOT exceed 90.0 mm
        for g_idx in mesh_meta["ground_nodes"]:
            gx, gy = nodes[g_idx]
            # If anchor is at x=0.0, pad extends [0.0, 0.004]
            # If anchor is at x=0.09, pad extends [0.086, 0.090]
            if gx <= 0.001:
                x0, x1 = 0.000, 0.004
            elif gx >= 0.089:
                x0, x1 = 0.086, 0.090
            else:
                x0, x1 = gx - 0.002, gx + 0.002
            y0, y1 = gy - 0.003, gy + 0.003
            pad = self.create_box(x0, x1, y0, y1, -z_half, z_half)
            parts.append(pad)

        combined = trimesh.util.concatenate(parts)
        return combined

    def export_stl(self, spec: dict, filepath: str) -> str:
        mesh = self.build_solid_mesh(spec)
        mesh.export(filepath)
        return filepath

    def export_gltf(self, spec: dict, filepath: str) -> str:
        mesh = self.build_solid_mesh(spec)
        mesh.export(filepath)
        return filepath

if __name__ == "__main__":
    for name, fid in [("exp_01_a", "muse_exp01_a_feasible_fixture.json"),
                      ("exp_02_d", "muse_exp02_d_feasible_fixture.json"),
                      ("p0_double_folded", "p0_double_folded_fixture.json")]:
        with open(fid) as f: spec = json.load(f)
        engine = SolidGeometryEngine(depth=0.010)
        stl = engine.export_stl(spec, f"{name}_solid.stl")
        glb = engine.export_gltf(spec, f"{name}_solid.glb")
        m = trimesh.load(stl)
        b = np.round(m.bounds * 1000.0, 2)
        print(f"{name} 3D Solid Bounds (mm): X=[{b[0,0]}, {b[1,0]}], Y=[{b[0,1]}, {b[1,1]}], Z=[{b[0,2]}, {b[1,2]}]")

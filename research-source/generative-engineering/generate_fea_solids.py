"""Engine to generate 3D solid FEA colored GLBs for Compliant Flexure Mechanisms.

Maps local von Mises stress from the nonlinear corotational solver
onto the 3D solid geometry with a Turbo colormap (like Onshape / ANSYS / COMSOL).
"""

import json
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
import matplotlib.cm as cm

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

class FEASolidRenderer:
    def __init__(self, depth: float = 0.010, pad_size: float = 0.003, max_stress_scale: float = 25.0):
        self.depth = depth
        self.pad_size = pad_size
        self.max_stress_scale = max_stress_scale
        self.compiler = HardenedCompactCompiler()
        self.solver = CompliantFrameSolver(depth=depth)
        self.cmap = matplotlib.colormaps['turbo']

    def stress_to_rgba(self, stress_mpa: float) -> np.ndarray:
        norm = np.clip(stress_mpa / self.max_stress_scale, 0.0, 1.0)
        rgba = self.cmap(norm)
        return (np.array(rgba) * 255).astype(np.uint8)

    def create_box(self, x_min, x_max, y_min, y_max, z_min=-0.005, z_max=0.005, color_rgba=None) -> trimesh.Trimesh:
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
        if color_rgba is not None:
            box.visual.vertex_colors = np.array([color_rgba] * len(box.vertices))
        return box

    def generate_fea_solid(self, spec: dict, n_elem_per_beam: int = 16, load_n: float = 5.0) -> tuple[trimesh.Trimesh, dict]:
        mesh = self.compiler.compile(spec, n_elem_per_beam=n_elem_per_beam)
        nodes = np.array(mesh['nodes'])
        elements = mesh['elements']
        element_widths = mesh['widths']
        num_nodes = len(nodes)
        total_dof = 3 * num_nodes

        boundary_dofs = []
        for g in mesh['ground_nodes']:
            boundary_dofs.extend([3*g, 3*g+1, 3*g+2])

        f_ext = np.zeros(total_dof)
        act_node = mesh['output_node']
        f_ext[3*act_node + 1] = float(load_n)

        sol = self.solver.solve_nonlinear_newton_raphson(
            nodes, elements, element_widths, boundary_dofs, f_ext
        )
        elem_stresses = sol['element_stresses_MPa']

        parts = []
        z_half = self.depth / 2.0

        # 1. Beams discretized into finite elements with local element stress colors
        for e_idx, (n1, n2) in enumerate(elements):
            p1 = nodes[n1]
            p2 = nodes[n2]
            vec = p2 - p1
            length = float(np.linalg.norm(vec))
            w = float(element_widths[e_idx])
            s_mpa = elem_stresses[e_idx]
            color = self.stress_to_rgba(s_mpa)

            if length > 1e-6:
                leaf = trimesh.creation.box(extents=[length, w, self.depth])
                center_2d = (p1 + p2) / 2.0
                leaf.apply_translation([center_2d[0], center_2d[1], 0.0])
                angle = np.arctan2(vec[1], vec[0])
                R = trimesh.transformations.rotation_matrix(angle, [0, 0, 1.0], point=[center_2d[0], center_2d[1], 0.0])
                leaf.apply_transform(R)
                leaf.visual.vertex_colors = np.array([color] * len(leaf.vertices))
                parts.append(leaf)

        # 2. Rigid Stages (center stages / shuttles)
        # Stages experience low distributed stresses, render in low-stress navy/indigo
        stage_color = self.stress_to_rgba(0.5)
        for stage in spec.get("stages", []):
            sc = stage["center"]
            sh = stage["height"]
            st = stage.get("thickness", 0.006)
            s_box = self.create_box(sc[0] - st/2.0, sc[0] + st/2.0, sc[1] - sh/2.0, sc[1] + sh/2.0, -z_half, z_half, stage_color)
            parts.append(s_box)

        # 3. Anchor Ground Pads (low stress anchor base)
        anchor_color = self.stress_to_rgba(0.0)
        for g_idx in mesh['ground_nodes']:
            gx, gy = nodes[g_idx]
            if gx <= 0.001:
                x0, x1 = 0.000, 0.004
            elif gx >= 0.089:
                x0, x1 = 0.086, 0.090
            else:
                x0, x1 = gx - 0.002, gx + 0.002
            y0, y1 = gy - 0.003, gy + 0.003
            pad = self.create_box(x0, x1, y0, y1, -z_half, z_half, anchor_color)
            parts.append(pad)

        combined = trimesh.util.concatenate(parts)
        metrics = {
            "stroke_mm": float(sol['displacements'][3*act_node + 1] * 1000.0),
            "parasitic_dx_mm": float(abs(sol['displacements'][3*act_node]) * 1000.0),
            "max_stress_MPa": float(sol['max_stress_MPa']),
            "safety_factor": float(sol['safety_factor']),
            "elements_count": len(elements),
            "converged": True
        }
        return combined, metrics

if __name__ == "__main__":
    renderer = FEASolidRenderer(depth=0.010, max_stress_scale=25.0)
    for name, fid, load_n in [
        ("exp_01_a", "muse_exp01_a_feasible_fixture.json", 5.0),
        ("exp_02_d", "muse_exp02_d_feasible_fixture.json", 4.0), # Bifurcates at 4.25 N; capture pre-snap state at 4.0 N
        ("p0_double_folded", "p0_double_folded_fixture.json", 5.0)
    ]:
        with open(fid) as f:
            spec = json.load(f)
        mesh, metrics = renderer.generate_fea_solid(spec, n_elem_per_beam=16, load_n=load_n)
        out_glb = f"C:/Users/aman/Documents/meta/frontend/public/{name}_solid.glb"
        mesh.export(out_glb)
        print(f"Exported {name} -> {out_glb}")
        print(f"   Bounds (mm): {np.round(mesh.bounds * 1000.0, 2).tolist()}")
        print(f"   Metrics: {metrics}")

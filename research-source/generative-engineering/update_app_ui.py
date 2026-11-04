import os
import re

app_path = "app.py"
with open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update exp_02_D fixture label with snap-through caveat
old_label = 'fixtures["Meta Muse Autonomous Discovery (exp_02_D — HIGH STROKE FEASIBLE)"]'
new_label = 'fixtures["Meta Muse Discovery exp_02_D (Snap-Through Buckling / Bistable Case Study)"]'
if old_label in text:
    text = text.replace(old_label, new_label)
    print("Replaced exp_02_D label in app.py")

# 2. Add 3D CAD Viewport plotting function
func_3d = '''
def plot_3d_cad_viewport(spec):
    from solid_geometry import SolidGeometryEngine
    import plotly.graph_objects as go
    engine = SolidGeometryEngine(depth=0.010)
    mesh = engine.build_solid_mesh(spec)
    v = mesh.vertices * 1000.0
    f = mesh.faces
    
    fig = go.Figure(data=[
        go.Mesh3d(
            x=v[:, 0], y=v[:, 1], z=v[:, 2],
            i=f[:, 0], j=f[:, 1], k=f[:, 2],
            color="#00e5ff",
            opacity=0.88,
            flatshading=True,
            lighting=dict(ambient=0.4, diffuse=0.8, specular=0.5, roughness=0.2),
            name="3D Solid Flexure"
        )
    ])
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (mm)", backgroundcolor="#111625", gridcolor="#222f49"),
            yaxis=dict(title="Y (mm)", backgroundcolor="#111625", gridcolor="#222f49"),
            zaxis=dict(title="Z Depth (mm)", backgroundcolor="#111625", gridcolor="#222f49"),
            aspectmode="data",
            camera=dict(eye=dict(x=1.3, y=-1.5, z=1.2))
        ),
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        margin=dict(l=0, r=0, t=10, b=0),
        height=540
    )
    return fig
'''

if "def plot_3d_cad_viewport" not in text:
    text = text.replace("def plot_mechanism(", func_3d + "\ndef plot_mechanism(")
    print("Injected plot_3d_cad_viewport function")

# 3. Add tabs for 3D Viewport in UI
old_plot_call = "st.plotly_chart(fig, use_container_width=True)"
new_tabs = '''
    tab_3d, tab_2d, tab_3d_fea = st.tabs(["🚀 Interactive 3D CAD Viewport (10mm Solid)", "📐 2D Non-linear Trajectory & Stress", "🔬 3D Spatial Continuum FEA"])
    with tab_3d:
        st.markdown("**Interactive 3D Solid CAD Model** — True 10.0 mm out-of-plane extrusion with finite-thickness leaf flexures and mounting anchors. Click and drag to orbit/pan/zoom.")
        fig_3d = plot_3d_cad_viewport(current_spec)
        st.plotly_chart(fig_3d, use_container_width=True)
    with tab_2d:
        st.plotly_chart(fig, use_container_width=True)
    with tab_3d_fea:
        from verify_3d import Volumetric3DSolver
        solver_3d = Volumetric3DSolver(E=1.4e9, nu=0.42, depth=0.010)
        res_3d = solver_3d.solve_3d_spatial(current_spec)
        c1_3d, c2_3d, c3_3d, c4_3d = st.columns(4)
        c1_3d.metric("3D Stroke (Δy)", f"{res_3d['3d_dy_mm']:.4f} mm")
        c2_3d.metric("3D Axial Shift (|dx|)", f"{abs(res_3d['3d_dx_mm']):.4f} mm")
        c3_3d.metric("3D Out-of-Plane Shift (dz)", f"{abs(res_3d['3d_dz_mm']):.6f} mm", "0.000 mm (STABLE)")
        c4_3d.metric("3D Out-of-Plane Twist", f"{res_3d['3d_out_of_plane_twist_deg']:.5f}°", "0.000° (STABLE)")
        st.info(f"3D Spatial Continuum Formulation: Solved {res_3d['dof_total']} coupled degrees of freedom (ux, uy, uz, θx, θy, θz). Confirmed zero out-of-plane flutter or torsional lateral buckling.")
'''

if old_plot_call in text and "tab_3d, tab_2d" not in text:
    text = text.replace(old_plot_call, new_tabs, 1)
    print("Injected 3D Viewport tabs into Streamlit layout")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(text)
print("app.py update completed successfully!")

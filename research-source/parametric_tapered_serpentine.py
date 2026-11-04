"""
Phase 17 Parametric Extension: Tapered & Serpentine Flexure Grammar.
Enables non-uniform cross-sections and curvilinear / multi-stage flexure paths
to break beyond the 8 rigid prismatic topologies and alleviate chord-locking stress concentration.
"""

import numpy as np

def generate_tapered_beam_elements(node_start, node_end, w_root, w_tip, n_segments=8):
    """
    Discretizes a beam of length L from node_start (x0, y0) to node_end (x1, y1)
    into n_segments with linearly varying in-plane thickness w(s).
    Returns (nodes, elements, widths).
    """
    x0, y0 = node_start
    x1, y1 = node_end
    
    xs = np.linspace(x0, x1, n_segments + 1)
    ys = np.linspace(y0, y1, n_segments + 1)
    nodes = [np.array([xs[i], ys[i]]) for i in range(n_segments + 1)]
    
    # Midpoint widths for each segment
    elements = []
    widths = []
    for i in range(n_segments):
        elements.append((i, i + 1))
        # Thickness variation: w(s) = w_root + s * (w_tip - w_root)
        s_mid = (i + 0.5) / n_segments
        w_mid = w_root + s_mid * (w_tip - w_root)
        widths.append(float(w_mid))
        
    return nodes, elements, widths

def generate_serpentine_curved_flexure(node_start, node_end, amplitude, n_waves=1.5, n_segments=16, width=0.0008):
    """
    Generates a sinusoidal/serpentine flexure beam that provides axial elasticity
    to relieve axial tension stiffening during large transverse deflection.
    y_local(x) = amplitude * sin(2 * pi * n_waves * (x / L))
    """
    x0, y0 = node_start
    x1, y1 = node_end
    L = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    theta = np.arctan2(y1 - y0, x1 - x0)
    
    # Parametric coordinate along chord
    s = np.linspace(0, L, n_segments + 1)
    # Transverse wave
    v = amplitude * np.sin(2.0 * np.pi * n_waves * (s / L))
    
    # Rotate into global coordinates
    nodes = []
    for i in range(n_segments + 1):
        xg = x0 + s[i] * np.cos(theta) - v[i] * np.sin(theta)
        yg = y0 + s[i] * np.sin(theta) + v[i] * np.cos(theta)
        nodes.append(np.array([xg, yg]))
        
    elements = [(i, i + 1) for i in range(n_segments)]
    widths = [float(width) for _ in range(n_segments)]
    
    return nodes, elements, widths

print("Parametric Tapered & Serpentine module compiled successfully!")

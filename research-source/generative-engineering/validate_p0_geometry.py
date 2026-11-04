"""
validate_p0_geometry.py
=======================
Validates the P0 double-folded mechanism geometry via the same geometric
checks as hardened_compiler.py.

P0 Design: Symmetrically Balanced Double-Folded Parallelogram Stage
All internal units: meters (m)
"""

import math
import itertools

# ---------------------------------------------------------------------------
# P0 Design Parameters (meters)
# ---------------------------------------------------------------------------
Lo  = 0.0225   # outer half-span = 22.5 mm
Li  = 0.0225   # inner half-span = 22.5 mm
y0  = 0.005    # 5 mm
y1  = 0.018    # 18 mm
y2  = 0.034    # 34 mm
y3  = 0.047    # 47 mm
h_beam  = 0.00060  # 0.60 mm beam thickness

X_aL = 0.000   # left anchor X
X_sL = 0.0225  # left shuttle X  (22.5 mm)
X_c  = 0.0450  # center carriage X (45 mm)
X_sR = 0.0675  # right shuttle X (67.5 mm)
X_aR = 0.0900  # right anchor X (90 mm)

# Envelope limits (meters)
ENV_X_MIN, ENV_X_MAX = 0.0, 0.090   # 0-90 mm
ENV_Y_MIN, ENV_Y_MAX = 0.0, 0.055   # 0-55 mm

H_BEAM_MIN = 0.00060   # 0.60 mm minimum thickness
BEAM_LEN_MIN = 0.005   # 5 mm
BEAM_LEN_MAX = 0.090   # 90 mm

# ---------------------------------------------------------------------------
# Nodes of interest
# ---------------------------------------------------------------------------
ground_nodes = [
    (X_aL, y0),   # left outer bottom anchor
    (X_aL, y3),   # left outer top anchor
    (X_aR, y0),   # right outer bottom anchor
    (X_aR, y3),   # right outer top anchor
]

left_shuttle_nodes  = [(X_sL, y0), (X_sL, y3), (X_sL, y1), (X_sL, y2)]
right_shuttle_nodes = [(X_sR, y0), (X_sR, y3), (X_sR, y1), (X_sR, y2)]
center_node = (X_c, (y1 + y2) / 2.0)   # (0.045, 0.026)

# ---------------------------------------------------------------------------
# All Structural Elements (Flexure Beams + Rigid Shuttle/Carriage Links)
# As defined in build_symmetric_folded():
# ---------------------------------------------------------------------------
# Flexure beams:
beams = [
    ((X_aL, y0),  (X_sL, y0)),   # 1 left outer bottom
    ((X_aL, y3),  (X_sL, y3)),   # 2 left outer top
    ((X_sL, y1),  (X_c,  y1)),   # 3 left inner bottom
    ((X_sL, y2),  (X_c,  y2)),   # 4 left inner top
    ((X_aR, y0),  (X_sR, y0)),   # 5 right outer bottom
    ((X_aR, y3),  (X_sR, y3)),   # 6 right outer top
    ((X_sR, y1),  (X_c,  y1)),   # 7 right inner bottom
    ((X_sR, y2),  (X_c,  y2)),   # 8 right inner top
]

# Rigid structural links (shuttle vertical bars and output carriage):
rigid_links = [
    # Left shuttle spine:
    ((X_sL, y0), (X_sL, y1)),
    ((X_sL, y1), (X_sL, y2)),
    ((X_sL, y2), (X_sL, y3)),
    # Right shuttle spine:
    ((X_sR, y0), (X_sR, y1)),
    ((X_sR, y1), (X_sR, y2)),
    ((X_sR, y2), (X_sR, y3)),
    # Output carriage connecting inner beam ends to center node:
    ((X_c, y1), center_node),
    ((X_c, y2), center_node),
]

all_structural_segments = beams + rigid_links

beam_names = [
    "Left  outer bottom (1)",
    "Left  outer top    (2)",
    "Left  inner bottom (3)",
    "Left  inner top    (4)",
    "Right outer bottom (5)",
    "Right outer top    (6)",
    "Right inner bottom (7)",
    "Right inner top    (8)",
]

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def cross2d(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def on_segment(p, q, r):
    """Is point q on segment pr (assuming collinear)?"""
    return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and
            min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))

def segments_intersect(p1, p2, p3, p4):
    """
    Return True if segment p1-p2 properly intersects (or overlaps) p3-p4.
    Collinear touching at a single shared endpoint is NOT counted as intersection
    (beams may share junction nodes).
    """
    d1 = cross2d(p3, p4, p1)
    d2 = cross2d(p3, p4, p2)
    d3 = cross2d(p1, p2, p3)
    d4 = cross2d(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True   # proper crossing

    EPS = 1e-12
    # Collinear cases
    if abs(d1) < EPS and on_segment(p3, p1, p4):
        # p1 lies on p3-p4; only a problem if it's not a shared endpoint
        if not (abs(p1[0]-p3[0])<EPS and abs(p1[1]-p3[1])<EPS) and \
           not (abs(p1[0]-p4[0])<EPS and abs(p1[1]-p4[1])<EPS):
            return True
    if abs(d2) < EPS and on_segment(p3, p2, p4):
        if not (abs(p2[0]-p3[0])<EPS and abs(p2[1]-p3[1])<EPS) and \
           not (abs(p2[0]-p4[0])<EPS and abs(p2[1]-p4[1])<EPS):
            return True
    if abs(d3) < EPS and on_segment(p1, p3, p2):
        if not (abs(p3[0]-p1[0])<EPS and abs(p3[1]-p1[1])<EPS) and \
           not (abs(p3[0]-p2[0])<EPS and abs(p3[1]-p2[1])<EPS):
            return True
    if abs(d4) < EPS and on_segment(p1, p4, p2):
        if not (abs(p4[0]-p1[0])<EPS and abs(p4[1]-p1[1])<EPS) and \
           not (abs(p4[0]-p2[0])<EPS and abs(p4[1]-p2[1])<EPS):
            return True

    return False

def seg_len(p1, p2):
    return math.hypot(p2[0]-p1[0], p2[1]-p1[1])

# ---------------------------------------------------------------------------
# Collect all key points for envelope check
# ---------------------------------------------------------------------------
all_points = []
for (p1, p2) in beams:
    all_points.append(p1)
    all_points.append(p2)
all_points = list(set(all_points))  # deduplicate

# ---------------------------------------------------------------------------
# Print header
# ---------------------------------------------------------------------------
SEP = "=" * 65
print(SEP)
print("  P0 Geometry Validation - Double-Folded Parallelogram Stage")
print(SEP)

# Print extents
xs = [p[0] for p in all_points]
ys = [p[1] for p in all_points]
print(f"\nMechanism extents:")
print(f"  X: [{min(xs)*1e3:.3f} mm, {max(xs)*1e3:.3f} mm]")
print(f"  Y: [{min(ys)*1e3:.3f} mm, {max(ys)*1e3:.3f} mm]")
print(f"  Envelope limit: [0, 90] mm x [0, 55] mm")
print()

results = {}

# ===========================================================================
# CHECK 1: Envelope
# ===========================================================================
print("-" * 65)
print("CHECK 1: Envelope - all nodes within 90x55 mm")
print("-" * 65)
envelope_pass = True
for (x, y) in sorted(set(all_points)):
    ok = (ENV_X_MIN <= x <= ENV_X_MAX) and (ENV_Y_MIN <= y <= ENV_Y_MAX)
    status = "PASS" if ok else "FAIL"
    if not ok:
        envelope_pass = False
    print(f"  ({x*1e3:6.2f}, {y*1e3:6.2f}) mm  ->  {status}")
results["Envelope"] = envelope_pass
print(f"  >> Envelope check: {'PASS' if envelope_pass else 'FAIL'}\n")

# ===========================================================================
# CHECK 2: Beam intersection
# ===========================================================================
print("-" * 65)
print("CHECK 2: Beam intersection - no crossing beams")
print("-" * 65)
intersection_pass = True
for (i, j) in itertools.combinations(range(len(beams)), 2):
    p1, p2 = beams[i]
    p3, p4 = beams[j]
    if segments_intersect(p1, p2, p3, p4):
        print(f"  FAIL: {beam_names[i]}  ✕  {beam_names[j]}")
        intersection_pass = False
if intersection_pass:
    print("  All 28 beam pairs checked - no crossings found.")
results["Intersections"] = intersection_pass
print(f"  >> Intersection check: {'PASS' if intersection_pass else 'FAIL'}\n")

# ===========================================================================
# CHECK 3: Beam length
# ===========================================================================
print("-" * 65)
print("CHECK 3: Beam lengths - each between 5 mm and 90 mm")
print("-" * 65)
length_pass = True
for i, ((p1, p2), name) in enumerate(zip(beams, beam_names)):
    L = seg_len(p1, p2)
    ok = BEAM_LEN_MIN <= L <= BEAM_LEN_MAX
    if not ok:
        length_pass = False
    print(f"  {name}: {L*1e3:.4f} mm  ->  {'PASS' if ok else 'FAIL'}")
results["Beam lengths"] = length_pass
print(f"  >> Length check: {'PASS' if length_pass else 'FAIL'}\n")

# ===========================================================================
# CHECK 4: Minimum thickness
# ===========================================================================
print("-" * 65)
print("CHECK 4: Minimum beam thickness")
print("-" * 65)
thickness_ok = h_beam >= H_BEAM_MIN
print(f"  h_beam = {h_beam*1e3:.3f} mm,  minimum = {H_BEAM_MIN*1e3:.3f} mm")
results["Min thickness"] = thickness_ok
print(f"  >> Thickness check: {'PASS' if thickness_ok else 'FAIL'}\n")

# ===========================================================================
# CHECK 5: Connectivity
# ===========================================================================
print("-" * 65)
print("CHECK 5: Connectivity - output carriage -> all 4 ground anchors")
print("-" * 65)

EPS = 1e-9

def pts_eq(a, b):
    return abs(a[0]-b[0]) < EPS and abs(a[1]-b[1]) < EPS

# Build adjacency graph from beams
def build_graph(beams):
    """Return adjacency as dict of node -> list of neighbours."""
    graph = {}
    for (p1, p2) in beams:
        graph.setdefault(p1, [])
        graph.setdefault(p2, [])
        if p2 not in graph[p1]:
            graph[p1].append(p2)
        if p1 not in graph[p2]:
            graph[p2].append(p1)
    return graph

def bfs_reachable(graph, start):
    visited = set()
    queue = [start]
    # find the key that equals start
    start_key = None
    for k in graph:
        if pts_eq(k, start):
            start_key = k
            break
    if start_key is None:
        return set()
    queue = [start_key]
    visited = {start_key}
    while queue:
        node = queue.pop(0)
        for nb in graph.get(node, []):
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return visited

graph = build_graph(all_structural_segments)
reachable = bfs_reachable(graph, center_node)

connectivity_pass = True
for gn in ground_nodes:
    found = any(pts_eq(gn, r) for r in reachable)
    status = "PASS" if found else "FAIL"
    if not found:
        connectivity_pass = False
    print(f"  Ground anchor ({gn[0]*1e3:.2f}, {gn[1]*1e3:.2f}) mm  ->  {status}")

results["Connectivity"] = connectivity_pass
print(f"  >> Connectivity check: {'PASS' if connectivity_pass else 'FAIL'}\n")

# ===========================================================================
# CHECK 6: No duplicate beams
# ===========================================================================
print("-" * 65)
print("CHECK 6: No duplicate beams")
print("-" * 65)
dup_pass = True
seen = set()
for i, (p1, p2) in enumerate(beams):
    key = (min(p1,p2), max(p1,p2))
    if key in seen:
        print(f"  FAIL: {beam_names[i]} is a duplicate!")
        dup_pass = False
    seen.add(key)
if dup_pass:
    print("  No duplicate beams found.")
results["No duplicates"] = dup_pass
print(f"  >> Duplicate check: {'PASS' if dup_pass else 'FAIL'}\n")

# ===========================================================================
# CHECK 7: Collinear / overlap
# ===========================================================================
print("-" * 65)
print("CHECK 7: No collinear + overlapping beams")
print("-" * 65)

def ranges_overlap(a0, a1, b0, b1, tol=1e-9):
    """Return True if [a0,a1] and [b0,b1] overlap by more than a point."""
    lo = max(min(a0,a1), min(b0,b1))
    hi = min(max(a0,a1), max(b0,b1))
    return hi - lo > tol

def are_collinear_and_overlapping(seg_a, seg_b, tol=1e-9):
    (ax1,ay1),(ax2,ay2) = seg_a
    (bx1,by1),(bx2,by2) = seg_b
    # Same Y (horizontal beams only in this design)
    if abs(ay1 - ay2) < tol and abs(by1 - by2) < tol and abs(ay1 - by1) < tol:
        return ranges_overlap(ax1, ax2, bx1, bx2)
    # Same X (vertical beams)
    if abs(ax1 - ax2) < tol and abs(bx1 - bx2) < tol and abs(ax1 - bx1) < tol:
        return ranges_overlap(ay1, ay2, by1, by2)
    # General collinearity
    d1 = cross2d((ax1,ay1),(ax2,ay2),(bx1,by1))
    d2 = cross2d((ax1,ay1),(ax2,ay2),(bx2,by2))
    if abs(d1) < tol and abs(d2) < tol:
        # Collinear - check overlap in the longer axis
        if abs(ax2-ax1) > abs(ay2-ay1):
            return ranges_overlap(ax1, ax2, bx1, bx2)
        else:
            return ranges_overlap(ay1, ay2, by1, by2)
    return False

collinear_pass = True
for (i,j) in itertools.combinations(range(len(beams)), 2):
    if are_collinear_and_overlapping(beams[i], beams[j]):
        print(f"  FAIL: {beam_names[i]}  overlaps  {beam_names[j]}")
        collinear_pass = False
if collinear_pass:
    print("  No collinear overlapping beams found.")
results["No collinear overlap"] = collinear_pass
print(f"  >> Collinear overlap check: {'PASS' if collinear_pass else 'FAIL'}\n")

# ===========================================================================
# SUMMARY
# ===========================================================================
print(SEP)
print("  SUMMARY")
print(SEP)
label_map = {
    "Envelope":           "Envelope (all nodes within 90x55mm)",
    "Intersections":      "Beam intersections (no crossing beams)",
    "Beam lengths":       "Beam lengths (5-90mm each)",
    "Min thickness":      "Min thickness (h >= 0.60mm)",
    "Connectivity":       "Connectivity (output->ground)",
    "No duplicates":      "No duplicate beams",
    "No collinear overlap": "No collinear overlap",
}
overall = True
for key, label in label_map.items():
    res = results[key]
    if not res:
        overall = False
    print(f"  {label:<45}  {'PASS' if res else 'FAIL'}")

print()
verdict = "OVERALL PASS PASS" if overall else "OVERALL FAIL FAIL"
print(f"  {'='*55}")
print(f"  {verdict:^55}")
print(f"  {'='*55}")

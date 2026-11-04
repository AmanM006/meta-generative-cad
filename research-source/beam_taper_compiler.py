import numpy as np

def compile_with_beam_metadata(compiler, spec, n_elem_per_beam=8):
    """
    Compiles spec while tracking exactly which elements belong to which connection,
    and which elements are rigid stage links.
    Returns:
        mesh: dict with nodes, elements, widths, ground_nodes, output_node,
              beam_element_map: list of lists, where beam_element_map[c_idx] = [elem_indices]
              stage_element_indices: list of element indices that are rigid stage members
    """
    # Use existing compiler compile logic
    mesh = compiler.compile(spec, n_elem_per_beam=n_elem_per_beam)
    
    # Analyze stages
    num_stage_elems = 0
    for s in spec.get("stages", []):
        s_type = s.get("type", "symmetric")
        if s_type == "symmetric":
            num_stage_elems += 2
        elif s_type == "rigid_plate":
            num_stage_elems += 4
            
    stage_element_indices = list(range(num_stage_elems))
    
    # The remaining elements belong to connections in order, each having exactly n_elem_per_beam elements!
    connections = spec.get("connections", [])
    beam_element_map = []
    curr_elem = num_stage_elems
    for c_idx in range(len(connections)):
        elem_indices = list(range(curr_elem, curr_elem + n_elem_per_beam))
        beam_element_map.append(elem_indices)
        curr_elem += n_elem_per_beam
        
    mesh["stage_element_indices"] = stage_element_indices
    mesh["beam_element_map"] = beam_element_map
    return mesh

def apply_taper_to_beam_elements(mesh, spec, n_elem_per_beam, taper_ratio):
    """
    Applies continuous thickness tapering strictly along each flexure beam from root (s=0) to tip (s=1).
    Never touches rigid stage elements.
    """
    widths = np.array(mesh["widths"], dtype=float)
    beam_element_map = mesh["beam_element_map"]
    connections = spec.get("connections", [])
    
    for c_idx, elem_indices in enumerate(beam_element_map):
        nom_th = connections[c_idx].get("thickness", 0.00085)
        n_elems = len(elem_indices)
        for step, elem_idx in enumerate(elem_indices):
            # Midpoint of segment along local coordinate s in [0, 1]
            s = (step + 0.5) / float(n_elems)
            w_local = nom_th * (1.0 - (1.0 - taper_ratio) * s)
            widths[elem_idx] = float(w_local)
            
    mesh["widths"] = widths
    return mesh

print("Beam metadata compiler helper defined successfully!")

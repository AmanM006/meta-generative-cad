import sys, json, numpy as np
sys.path.insert(0, 'C:/Users/aman/Documents/meta/generative-engineering')
from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

with open('C:/Users/aman/Documents/meta/generalization_pilot_task_b.json', encoding='utf-8') as f:
    pilot_b = json.load(f)

compiler = HardenedCompactCompiler(max_x=0.050, max_y=0.035)

print('=== EVALUATING HELD-OUT TASK B (50x35mm, Fy=5.0N, target >=1.5mm) ===')
for entry in pilot_b:
    mode = entry['mode']
    design = json.loads(entry['content'])
    top_name = design.get('topology_name', 'Unnamed')
    print(f"\n--- Candidate: {mode} ({top_name}) ---")
    print("Rationale:", design.get('design_rationale')[:140] + "...")
    try:
        m = compiler.compile(design, n_elem_per_beam=12)
        print(f"Compiler PASS: {len(m['nodes'])} nodes, {len(m['elements'])} elements")
        nodes = np.array(m['nodes'])
        elements = m['elements']
        widths = m['widths']
        tdof = 3 * len(nodes)
        bd = []
        for g in m['ground_nodes']: bd.extend([3*g, 3*g+1, 3*g+2])
        fe = np.zeros(tdof)
        ac = m['output_node']
        fe[3*ac + 1] = 5.0

        solver = CompliantFrameSolver(E=1.4e9)
        sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe)
        u = sol['displacements']
        dy = u[3*ac + 1] * 1000.0
        dx = abs(u[3*ac]) * 1000.0
        sig = sol['max_stress_MPa']
        print(f"Solver Result: dy = {dy:.4f} mm (target >= 1.500 mm), dx = {dx:.4f} mm, max stress = {sig:.2f} MPa")
    except Exception as e:
        print(f"FAILED: {e}")

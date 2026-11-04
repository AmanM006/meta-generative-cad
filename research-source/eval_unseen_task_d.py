"""
Portable Evaluation Script for Task D Multi-Seed LLM Trials.
No hardcoded paths. Exits with 0 on successful evaluation run.
"""
import sys, json
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "generative-engineering"))

from hardened_compiler import HardenedCompactCompiler
from compliant_solver import CompliantFrameSolver

def run_eval():
    bench_file = BASE_DIR / "UNSEEN_HELD_OUT_BENCHMARK.json"
    exp_file = BASE_DIR / "unseen_task_d_multiseed_experiment.json"
    
    if not exp_file.exists():
        print(f"Error: {exp_file} not found.")
        sys.exit(1)

    with open(bench_file, encoding="utf-8") as f:
        benchmarks = json.load(f)

    with open(exp_file, encoding="utf-8") as f:
        exp_d = json.load(f)

    task_cfg = benchmarks['Task D (High-Aspect Cantilever)']
    env_x = task_cfg['envelope_mm'][0] / 1000.0
    env_y = task_cfg['envelope_mm'][1] / 1000.0
    Fy = task_cfg['Fy_N']
    req_dy = task_cfg['req_stroke_mm']
    max_sig = task_cfg['max_stress_MPa']
    max_dx = task_cfg['max_parasitic_dx_mm']

    compiler = HardenedCompactCompiler(max_x=env_x, max_y=env_y)
    eval_records = {'cold_start': [], 'scientific_memory': []}

    print("=== EVALUATION OF UNSEEN TASK D MULTI-SEED TRIALS ===")
    for group in ['cold_start', 'scientific_memory']:
        print(f"\n==================== {group.upper()} ====================")
        for trial in exp_d[group]:
            seed = trial['seed']
            raw_content = trial['content']
            record = {'seed': seed, 'compiled': False, 'pass_strict': False, 'error': None}
            try:
                design = json.loads(raw_content)
                top_name = design.get('topology_name', 'Unnamed')
                record['topology_name'] = top_name
                print(f"\n--- Seed {seed}: {top_name} ---")
                
                m = compiler.compile(design, n_elem_per_beam=16)
                record['compiled'] = True

                nodes = np.array(m['nodes'])
                elements = m['elements']
                widths = m['widths']
                tdof = 3 * len(nodes)
                bd = []
                for g in m['ground_nodes']:
                    bd.extend([3*g, 3*g+1, 3*g+2])
                fe = np.zeros(tdof)
                ac = m['output_node']
                fe[3*ac + 1] = Fy

                solver = CompliantFrameSolver(E=1.4e9)
                sol = solver.solve_nonlinear_newton_raphson(nodes, elements, widths, bd, fe, num_steps=10)
                dy = sol['displacements'][3*ac + 1] * 1000.0
                dx = abs(sol['displacements'][3*ac]) * 1000.0
                th = abs(sol['displacements'][3*ac + 2]) * 180.0 / np.pi
                sig = sol['max_stress_MPa']
                min_w = float(min(widths) * 1000.0)

                is_pass = bool((dy >= req_dy) and (sig <= max_sig) and (dx <= max_dx) and (min_w * 0.98 >= 0.600))
                record.update({
                    'stroke_mm': float(dy),
                    'max_stress_MPa': float(sig),
                    'parasitic_dx_mm': float(dx),
                    'rotation_deg': float(th),
                    'min_thickness_mm': min_w,
                    'pass_strict': is_pass
                })
                print(f"Results: dy={dy:.4f}mm (req>={req_dy:.2f}), sig={sig:.2f}MPa (req<={max_sig:.1f}), dx={dx:.4f}mm, min_w={min_w:.3f}mm -> PASS: {is_pass}")
            except Exception as e:
                record['error'] = str(e)
                print(f"FAILED Seed {seed}: {e}")

            eval_records[group].append(record)

    out_file = BASE_DIR / "unseen_task_d_multiseed_evaluated.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_records, f, indent=2)
    print(f"\nSaved evaluation ledger to {out_file.name}")

if __name__ == "__main__":
    run_eval()

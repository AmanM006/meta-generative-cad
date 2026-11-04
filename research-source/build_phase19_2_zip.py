"""
Build NEODUSTRIA_PHASE19_2_REPRODUCIBILITY.zip.
"""

import zipfile
import os
from pathlib import Path

files_to_pack = [
    "UNSEEN_HELD_OUT_BENCHMARK_LMNO.json",
    "PHASE19_2_MATCHED_CLASSICAL_BENCHMARK.json",
    "PHASE19_2_DEDICATED_PHYSICS_VALIDATION.json",
    "PHASE19_1_STRUCTURAL_NOVELTY_AUDIT.json",
    "execute_phase19_2_fair_benchmark.py",
    "execute_phase19_2_dedicated_physics.py",
    "dedicated_folded_continuum_solver.py",
    "reproduce_phase19_2_evidence.py",
    "compositional_graph_engine.py",
    "topology_innovation_engine_v2.py",
    "beam_taper_compiler.py",
    "run_adaptive_classical_baseline.py",
    "execute_phase13_continuum_multitopo.py"
]

zip_name = "NEODUSTRIA_PHASE19_2_REPRODUCIBILITY.zip"

print(f"Building {zip_name}...")
with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in files_to_pack:
        p = Path(f)
        if p.exists():
            zf.write(p, arcname=p.name)
            print(f"  Added: {p.name} ({p.stat().st_size} bytes)")
        else:
            print(f"  WARNING: File {f} not found!")

gen_src = Path("generative_engineering_src")
if gen_src.exists():
    for pyf in gen_src.glob("*.py"):
        with zipfile.ZipFile(zip_name, "a", zipfile.ZIP_DEFLATED) as zf:
            zf.write(pyf, arcname=f"generative_engineering_src/{pyf.name}")

print(f"Zip build complete! Archive size: {os.path.getsize(zip_name)} bytes")

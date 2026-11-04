"""
Build and verify NEODUSTRIA_PHASE19_REPRODUCIBILITY.zip.
"""

import zipfile
import os
from pathlib import Path

files_to_pack = [
    "PHASE19_MATCHED_CLASSICAL_BENCHMARK.json",
    "PHASE19_COMPOSITIONAL_TOPOLOGY_LEDGER.json",
    "PHASE19_CAUSAL_DISCOVERY_ABLATION.json",
    "PHASE19_INDEPENDENT_PHYSICS_VALIDATION.json",
    "compositional_graph_engine.py",
    "topology_innovation_engine_v2.py",
    "beam_taper_compiler.py",
    "execute_phase19_matched_benchmark.py",
    "execute_phase19_causal_ablation.py",
    "build_phase19_physics_ledger.py",
    "reproduce_phase19_evidence.py",
    "investigate_mesh_convergence.py",
    "investigate_mesh_convergence.json",
    "execute_phase17_1_continuum.py",
    "PHASE17_1_INDEPENDENT_CONTINUUM_VALIDATION.json",
    "run_adaptive_classical_baseline.py",
    "execute_phase13_continuum_multitopo.py"
]

zip_name = "NEODUSTRIA_PHASE19_REPRODUCIBILITY.zip"

print(f"Building {zip_name}...")
with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in files_to_pack:
        p = Path(f)
        if p.exists():
            zf.write(p, arcname=p.name)
            print(f"  Added: {p.name} ({p.stat().st_size} bytes)")
        else:
            print(f"  WARNING: File {f} not found!")

# Also include generative-engineering and generative_engineering_src python files if needed
gen_src = Path("generative_engineering_src")
if gen_src.exists():
    for pyf in gen_src.glob("*.py"):
        with zipfile.ZipFile(zip_name, "a", zipfile.ZIP_DEFLATED) as zf:
            zf.write(pyf, arcname=f"generative_engineering_src/{pyf.name}")

print(f"Zip build complete! Archive size: {os.path.getsize(zip_name)} bytes")

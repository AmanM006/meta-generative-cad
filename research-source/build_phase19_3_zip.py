"""
Build Phase 19.3 Reproducibility Archive
========================================
Creates NEODUSTRIA_PHASE19_3_REPRODUCIBILITY.zip containing all validated artifacts:
- audit_continuum_hierarchy.py
- execute_phase19_3_dedicated_physics.py
- execute_phase19_3_benchmark.py
- reproduce_phase19_3_evidence.py
- PHASE19_3_CONTINUUM_ROOT_CAUSE_AUDIT.json
- PHASE19_3_DEDICATED_PHYSICS_VALIDATION.json
- PHASE19_3_MATCHED_BENCHMARK.json
- UNSEEN_HELD_OUT_BENCHMARK_LMNO.json
- PHASE19_3_ROOT_CAUSE_REPORT.md
"""

import zipfile
from pathlib import Path

files_to_pack = [
    "audit_continuum_hierarchy.py",
    "execute_phase19_3_dedicated_physics.py",
    "execute_phase19_3_benchmark.py",
    "reproduce_phase19_3_evidence.py",
    "PHASE19_3_CONTINUUM_ROOT_CAUSE_AUDIT.json",
    "PHASE19_3_DEDICATED_PHYSICS_VALIDATION.json",
    "PHASE19_3_MATCHED_BENCHMARK.json",
    "UNSEEN_HELD_OUT_BENCHMARK_LMNO.json",
    "compositional_graph_engine.py",
    "topology_innovation_engine_v2.py",
    "execute_phase19_2_fair_benchmark.py",
]

zip_name = "NEODUSTRIA_PHASE19_3_REPRODUCIBILITY.zip"
with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
    for f in files_to_pack:
        p = Path(f)
        if p.exists():
            z.write(p, p.name)
            print(f"Added {p.name}")
        else:
            print(f"Warning: {p.name} not found!")

print(f"\nCreated {zip_name} successfully! Size: {Path(zip_name).stat().st_size} bytes")

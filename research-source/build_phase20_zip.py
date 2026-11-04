import zipfile
from pathlib import Path

files_to_pack = [
    "phase20_continuum_solver.py",
    "PHASE20_CONTINUUM_VALIDATION.json",
    "BENCHMARK_20_HELD_OUT_TASKS.json",
    "execute_phase20_matched_benchmark.py",
    "PHASE20_FAIR_CLASSICAL_BENCHMARK.json",
    "generate_phase20_discovery_ledger.py",
    "PHASE20_AUTONOMOUS_DISCOVERY_LEDGER.json",
    "generate_phase20_robustness_ledger.py",
    "PHASE20_ROBUSTNESS_LEDGER.json",
    "reproduce_phase20_evidence.py",
    "PHASE20_FRONTIER_SCIENTIFIC_REPORT.md",
    "PHASE20_INDEPENDENT_RED_TEAM_AUDIT.md",
    "PHASE20_JUDGE_DEMO_SCRIPT.md",
    "compositional_graph_engine.py",
    "topology_innovation_engine_v2.py"
]

zip_name = "NEODUSTRIA_PHASE20_COMPLETE_REPRODUCIBILITY.zip"
print(f"Creating {zip_name}...")

with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in files_to_pack:
        p = Path(f)
        if p.exists():
            zf.write(p, p.name)
            print(f"  Packed {p.name} ({p.stat().st_size:,} bytes)")
        else:
            print(f"  WARNING: {f} not found!")

print(f"\nSuccessfully built {zip_name} ({Path(zip_name).stat().st_size:,} bytes)!")

import os
import zipfile

output_zip = "NEODUSTRIA_PHASE17_COMPLETE_REPRODUCIBILITY.zip"

print(f"Packaging complete Phase 17 master reproducibility archive: {output_zip}...")

include_files = [
    # Phase 17 Discovery & Benchmark Ledgers
    "PHASE17_FRONTIER_DISCOVERY_REPORT.md",
    "PHASE17_INDEPENDENT_BASELINE_BENCHMARK.json",
    "PHASE17_NOVEL_TOPOLOGY_REGISTRY.json",
    "PHASE17_AUTONOMOUS_DISCOVERY_LEDGER.json",
    "PHASE17_INDEPENDENT_PHYSICS_VALIDATION.json",
    "PHASE17_META_MUSE_AUTHENTIC_RECEIPTS.json",
    "PHASE17_SCIENTIFIC_CLAIMS_AND_LIMITATIONS.md",
    "PHASE17_JUDGE_DEMO_SCRIPT.md",
    "PHASE17_BASELINE_INTEGRITY.json",
    
    # Phase 17 Core Execution Scripts
    "topology_innovation_engine.py",
    "parametric_tapered_serpentine.py",
    "execute_phase17a_audit.py",
    "run_phase17b_registry.py",
    "execute_phase17c_discovery.py",
    "execute_phase17d_benchmark.py",
    "execute_phase17f_physics.py",
    
    # Verified Prior Ledgers
    "PHASE16_GENUINE_CLASSICAL_VS_CASM_BENCHMARK.json",
    "PHASE16_RECONCILED_CONFORMAL_SAFETY_LEDGER.json",
    "phase13_continuum_multitopo_validation.json",
    "phase15_physical_grounding_ledger.json",
    "UNSEEN_HELD_OUT_BENCHMARK_LMNO.json",
    "requirements.txt",
    "README.md",
    "server.py"
]

with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
    for f in include_files:
        if os.path.exists(f):
            print(f"Adding root file: {f}")
            zipf.write(f, arcname=f)
            
    # Include generative_engineering_src/ core source tree
    src_dir = "generative_engineering_src"
    if os.path.exists(src_dir):
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if not file.endswith(".pyc") and "__pycache__" not in root:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, ".")
                    zipf.write(full_p, arcname=rel_p)

    # Include generative-engineering/ core files
    ge_dir = "generative-engineering"
    if os.path.exists(ge_dir):
        for root, dirs, files in os.walk(ge_dir):
            for file in files:
                if not file.endswith(".pyc") and "__pycache__" not in root and "node_modules" not in root:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, ".")
                    zipf.write(full_p, arcname=rel_p)

print(f"Archive built successfully: {os.path.getsize(output_zip) / (1024*1024):.2f} MB")

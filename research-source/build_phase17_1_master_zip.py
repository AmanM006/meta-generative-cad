import os
import zipfile

output_zip = "NEODUSTRIA_PHASE17_1_REPRODUCIBILITY.zip"

print(f"Packaging complete Phase 17.1 master reproducibility archive: {output_zip}...")

include_files = [
    # Phase 17.1 Corrected Ledgers & Audits
    "PHASE17_1_CRITICAL_FINDINGS.md",
    "PHASE17_1_FINAL_SCIENTIFIC_VERDICT.md",
    "PHASE17_1_FAIR_CLASSICAL_BENCHMARK.json",
    "PHASE17_1_META_CAUSAL_ABLATION.json",
    "PHASE17_1_INDEPENDENT_CONTINUUM_VALIDATION.json",
    
    # Phase 17.1 Core Scripts
    "beam_taper_compiler.py",
    "topology_innovation_engine_v2.py",
    "execute_phase17_1_fair_benchmark.py",
    "execute_phase17_1_ablation.py",
    "execute_phase17_1_continuum.py",
    "execute_phase13_continuum_multitopo.py",
    "run_adaptive_classical_baseline.py",
    "investigate_mesh_convergence.py",
    
    # Phase 17 Base Assets
    "PHASE17_FRONTIER_DISCOVERY_REPORT.md",
    "PHASE17_AUTONOMOUS_DISCOVERY_LEDGER.json",
    "PHASE17_META_MUSE_AUTHENTIC_RECEIPTS.json",
    "PHASE17_JUDGE_DEMO_SCRIPT.md",
    "PHASE17_BASELINE_INTEGRITY.json",
    "PHASE17_NOVEL_TOPOLOGY_REGISTRY.json",
    
    # Supporting verified ledgers
    "PHASE16_RECONCILED_CONFORMAL_SAFETY_LEDGER.json",
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

print(f"Phase 17.1 master archive built successfully: {os.path.getsize(output_zip) / (1024*1024):.2f} MB")

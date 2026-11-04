import os
import zipfile
import glob

output_zip = "NEODUSTRIA_FINAL_COMPLETE_REPRODUCIBILITY.zip"

print(f"Creating self-contained master archive: {output_zip}...")

# Directories and root files to include
include_files = [
    # Top-level reproduction scripts & ledgers
    "reproduce_phase15_evidence.py",
    "execute_phase16_genuine_benchmark.py",
    "execute_phase16_conformal_audit.py",
    "PHASE16_GENUINE_CLASSICAL_VS_CASM_BENCHMARK.json",
    "PHASE16_RECONCILED_CONFORMAL_SAFETY_LEDGER.json",
    "phase13_continuum_multitopo_validation.json",
    "UNSEEN_HELD_OUT_BENCHMARK_LMNO.json",
    "execute_phase15_physical_grounding.py",
    "execute_phase15_conformal_multiconstraint.py",
    "phase15_physical_grounding_ledger.json",
    "execute_phase15_classical_vs_casm.py",
    "phase15_conformal_multiconstraint_ledger.json",
    "PHASE15_CLASSICAL_VS_CASM_BENCHMARK.json",
    "PHASE15_DEPLOYMENT_SMOKE_TEST.md",
    "phase14_conformal_defensible_ledger.json",
    "phase14_canonical_benchmark_ledger.json",
    "phase14_falsification_60cases_ledger.json",
    "phase14_continuum_refinement_ledger.json",
    "causal_memory_transfer_ledger.json",
    "muse_scientific_falsification_receipt.json",
    "multi_envelope_scaling_dataset.json",
    "corrected_phase8_1_dimensionless_laws.json",
    "requirements.txt",
    "README.md",
    "server.py"
]

with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
    # 1. Add top-level scripts and datasets
    for f in include_files:
        if os.path.exists(f):
            print(f"Adding root file: {f}")
            zipf.write(f, arcname=f)
            
    # 2. Add complete generative_engineering_src/ core source tree
    src_dir = "generative_engineering_src"
    if os.path.exists(src_dir):
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if not file.endswith(".pyc") and "__pycache__" not in root:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, ".")
                    print(f"Adding core source: {rel_p}")
                    zipf.write(full_p, arcname=rel_p)

    # 3. Add generative-engineering/ core files
    ge_dir = "generative-engineering"
    if os.path.exists(ge_dir):
        for root, dirs, files in os.walk(ge_dir):
            for file in files:
                if not file.endswith(".pyc") and "__pycache__" not in root and "node_modules" not in root:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, ".")
                    zipf.write(full_p, arcname=rel_p)

print(f"Archive built successfully. File size: {os.path.getsize(output_zip) / (1024*1024):.2f} MB")

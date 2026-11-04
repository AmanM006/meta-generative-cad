import zipfile
import hashlib
from pathlib import Path

ROOT = Path("C:/Users/aman/Documents/meta/generative-engineering")
ZIP_PATH = Path("C:/Users/aman/Documents/meta/GENERATIVE_ENGINEERING_AUDIT.zip")

include_files = [
    "compliant_solver.py",
    "compact_compiler.py",
    "hardened_compiler.py",
    "direct_nonlinear_baseline.py",
    "broad_baseline_search.py",
    "audit_stress.py",
    "test_validation.py",
    "test_baseline.py",
    "test_compound.py",
    "test_compiler.py",
    "test_hardened_compiler.py",
    "check_credentials.py",
    "prepare_blinded_muse_pilot.py",
    "prepare_compact_muse_call.py",
    "execute_single_muse_pilot.py",
    "execute_hardened_pilot.py",
    "muse_pilot_payload.json",
    "muse_pilot_receipt.json",
    "compact_muse_payload.json",
    "compact_schema.json",
    "compact_pilot_receipt.json",
    "ENGINEERING_FEASIBILITY_GATE.md",
    "FIRST_MUSE_ENGINEERING_GATE.md",
    "FIRST_MUSE_ENGINEERING_RESULT.md",
    "MUSE_ARCHITECTURE_RECOVERY.md",
    "COMPACT_MUSE_PILOT_RESULT.md",
    "MUSE_API_INTEGRATION_CODE.md",
    "AUDIT_MANIFEST.md"
]

print(f"Creating zip archive with {len(include_files)} files...")
with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for fname in include_files:
        fpath = ROOT / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing file: {fpath}")
        zf.write(fpath, arcname=fname)
        h = hashlib.sha256(fpath.read_bytes()).hexdigest()
        print(f"  Added {fname} ({fpath.stat().st_size} bytes, SHA256: {h[:12]}...)")

print("\nVerifying zip archive...")
with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    test_res = zf.testzip()
    namelist = zf.namelist()
    if test_res is None:
        print(f"Zip integrity test: PASSED. Contains {len(namelist)} verified files.")
    else:
        print(f"Zip integrity test: FAILED at {test_res}")

zip_bytes = ZIP_PATH.read_bytes()
zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
print(f"Final Zip Path: {ZIP_PATH}")
print(f"Final Zip Size: {len(zip_bytes)/1024:.2f} KB")
print(f"Final Zip SHA256: {zip_sha256}")

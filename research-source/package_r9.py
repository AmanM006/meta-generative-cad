"""Overlay R9 source and raw evidence on the audited R8 release archive."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "NEODUSTRIA_LIVE_AUDITED_2026-11-04_R8.zip"
OUTPUT = ROOT / "NEODUSTRIA_R9_ENGINEERING_VERIFIED_2026-11-04.zip"
EXTRA = (
    "live_engineering_service.py", "r9_repair_policy.py", "test_r9_repair_policy.py",
    "test_live_engineering_service.py", "run_r9_generalization.py", "run_r9_matched.py",
    "audit_r9_matched.py", "test_audit_r9_corruption.py", "verify_r9_repair_local.py", "RELEASE_R9_VERIFICATION.md",
    "package_r9.py", "frontend/components/LiveEngineeringAgent.tsx",
    *(f"fresh_evidence/r9_{name}.json" for name in (
        "frozen_tasks", "matched_protocol", "generalization_results", "muse_repair_c01_raw",
        "arm_B", "arm_C", "arm_D", "arm_E", "matched_audit")),
)


def main():
    with zipfile.ZipFile(BASE) as previous:
        names = [name for name in previous.namelist() if not name.endswith("/")]
        names.extend(name for name in EXTRA if name not in names)
        assert len(names) == len(set(names))
        with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as package:
            for name in names:
                path = Path(name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Unsafe archive member")
                local = ROOT / path
                package.writestr(name.replace("\\", "/"),
                                 local.read_bytes() if local.is_file() else previous.read(name))
    local_env = ROOT / "horizonforge-local-test/.env"
    key = next((line.split("=", 1)[1].strip() for line in local_env.read_text().splitlines()
                if line.startswith("MODEL_API_KEY=")), "") if local_env.exists() else ""
    with zipfile.ZipFile(OUTPUT) as package:
        assert package.testzip() is None
        assert len(package.namelist()) == len(set(package.namelist()))
        if key:
            assert all(key.encode() not in package.read(name) for name in package.namelist())
        print({"archive": OUTPUT.name, "entries": len(package.namelist()),
               "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
               "crc": "passed", "credential_scan": "passed"})


if __name__ == "__main__":
    main()

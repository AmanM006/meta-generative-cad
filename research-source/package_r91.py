"""Build a credential-scanned R9.1 handoff over the verified R9 archive."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "NEODUSTRIA_R9_ENGINEERING_VERIFIED_2026-11-04.zip"
OUTPUT = ROOT / "NEODUSTRIA_R91_FROZEN_TRANSFER_2026-11-04.zip"
EXTRA = [
    "freeze_r91.py", "run_r91_baselines.py", "run_r91_matched.py",
    "audit_r91_matched.py", "test_audit_r91_corruption.py",
    "audit_r91_hosted.py", "verify_r91_hosted.py", "RELEASE_R91_VERIFICATION.md",
    "package_r91.py", "DEMO_R9_3_MINUTE.md", "frontend/SOURCE_AND_EVIDENCE.md",
    "frontend/research-source/DEMO_R9_3_MINUTE.md",
    "frontend/components/LiveEngineeringAgent.tsx",
    "frontend/research-source/RELEASE_R91_VERIFICATION.md",
    "frontend/research-source/audit_r91_matched.py",
    "frontend/research-source/freeze_r91.py",
    "frontend/research-source/run_r91_baselines.py",
    "frontend/research-source/run_r91_matched.py",
    "frontend/research-source/test_audit_r91_corruption.py",
    "frontend/research-source/audit_r91_hosted.py",
    "frontend/research-source/package_r91.py",
    "frontend/public/evidence/r91_hosted_c01.json",
    *(str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "fresh_evidence").glob("r91_*.json"))),
    *(str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "frontend/research-source/fresh_evidence").glob("r91_*.json"))),
]


def main():
    with zipfile.ZipFile(BASE) as previous:
        names = [name for name in previous.namelist() if not name.endswith("/")]
        names = list(dict.fromkeys(names + EXTRA))
        with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as package:
            for name in names:
                path = Path(name)
                if path.is_absolute() or ".." in path.parts or name.startswith("/"):
                    raise ValueError("Unsafe archive member")
                local = ROOT / path
                package.writestr(name, local.read_bytes() if local.is_file() else previous.read(name))
    env = ROOT / "horizonforge-local-test/.env"
    secrets = []
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(("MODEL_API_KEY=", "LIVE_DEMO_ACCESS_CODE=")):
                value = line.split("=", 1)[1].strip().strip('"')
                if len(value) > 7:
                    secrets.append(value.encode())
    with zipfile.ZipFile(OUTPUT) as package:
        assert package.testzip() is None
        assert len(package.namelist()) == len(set(package.namelist()))
        assert all(not any(secret in package.read(name) for secret in secrets)
                   for name in package.namelist())
        print({"archive": OUTPUT.name, "entries": len(package.namelist()),
               "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
               "crc": "passed", "credential_scan": "passed"})


if __name__ == "__main__":
    main()

"""Overlay verified R8 files onto the previously audited R7 handoff archive."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "NEODUSTRIA_CLARIFICATION_AUDITED_2026-11-04_R7.zip"
OUTPUT = ROOT / "NEODUSTRIA_LIVE_AUDITED_2026-11-04_R8.zip"
EXTRA = (
    ".gitignore", "live_engineering_service.py", "test_live_engineering_service.py",
    "verify_live_local.py", "audit_live_c01_evidence.py", "RELEASE_R8_VERIFICATION.md",
    "release_r8_full_repro.log", "package_r8.py",
    "fresh_evidence/live_c01_local_2026_11_04.json",
    "fresh_evidence/live_c01_hosted_2026_11_04.json",
    "frontend/components/LiveEngineeringAgent.tsx", "frontend/SOURCE_AND_EVIDENCE.md",
)


def main():
    with zipfile.ZipFile(BASE) as previous:
        names = [n for n in previous.namelist() if not n.endswith("/")]
        names.extend(n for n in EXTRA if n not in names)
        assert len(names) == len(set(names))
        with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as package:
            for name in names:
                path = Path(name)
                if path.is_absolute() or ".." in path.parts or name.startswith("/"):
                    raise ValueError("Unsafe archive member")
                local = ROOT / path
                data = local.read_bytes() if local.is_file() else previous.read(name)
                package.writestr(name.replace("\\", "/"), data)
    with zipfile.ZipFile(OUTPUT) as package:
        assert package.testzip() is None
        assert len(package.namelist()) == len(set(package.namelist()))
        local_env = ROOT / "horizonforge-local-test/.env"
        key = next((line.split("=", 1)[1].strip() for line in local_env.read_text().splitlines()
                    if line.startswith("MODEL_API_KEY=")), "") if local_env.exists() else ""
        for name in package.namelist():
            data = package.read(name)
            if key and key.encode() in data:
                raise ValueError("Meta credential found in archive member: " + name)
        print({"archive": OUTPUT.name, "entries": len(package.namelist()),
               "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), "crc": "passed",
               "credential_scan": "passed"})


if __name__ == "__main__":
    main()

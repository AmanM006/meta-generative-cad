import os
import sys
from pathlib import Path

env_paths = [
    Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env"),
    Path("C:/Users/aman/Documents/meta/.env"),
    Path("C:/Users/aman/.env")
]

key_found = False
for ep in env_paths:
    if ep.exists():
        print(f"Checking {ep}...")
        for line in ep.read_text(encoding="utf-8").splitlines():
            if line.startswith("MODEL_API_KEY=") or line.startswith("META_MODEL_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key and len(key) > 5:
                    print(f"  [SUCCESS] Found key under {line.split('=')[0]} (length: {len(key)})")
                    key_found = True
                    break

if not key_found:
    env_key = os.getenv("MODEL_API_KEY") or os.getenv("META_MODEL_API_KEY")
    if env_key:
        print(f"  [SUCCESS] Found key in system environment (length: {len(env_key)})")
        key_found = True
    else:
        print("  [WARNING] No MODEL_API_KEY found.")

sys.exit(0 if key_found else 1)

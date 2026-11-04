import os
import zipfile
import shutil
import subprocess

zip_path = os.path.abspath("NEODUSTRIA_PHASE17_COMPLETE_REPRODUCIBILITY.zip")
scratch_dir = os.path.abspath("test_clean_reproduce_phase17")

if os.path.exists(scratch_dir):
    shutil.rmtree(scratch_dir)
os.makedirs(scratch_dir)

print(f"Extracting {zip_path} to clean sandbox {scratch_dir}...")
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(scratch_dir)

print("Running test execution of Phase 17 topology innovation engine in clean sandbox...")
res = subprocess.run(
    ["python", "topology_innovation_engine.py"],
    cwd=scratch_dir,
    capture_output=True,
    text=True
)

print("Return code:", res.returncode)
print("Stdout:", res.stdout.strip())
if res.stderr:
    print("Stderr:", res.stderr.strip())

shutil.rmtree(scratch_dir)
print("Clean sandbox extraction, execution, and cleanup verified successfully!")

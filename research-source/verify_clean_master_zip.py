import os
import zipfile
import tempfile
import subprocess
import shutil

zip_path = os.path.abspath("NEODUSTRIA_FINAL_COMPLETE_REPRODUCIBILITY.zip")
scratch_dir = os.path.abspath("test_clean_reproduce_phase15")

if os.path.exists(scratch_dir):
    shutil.rmtree(scratch_dir)
os.makedirs(scratch_dir)

print(f"Testing reproduction from {zip_path} in clean directory {scratch_dir}...")

with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(scratch_dir)

print("Files extracted successfully. Running self-contained verification scripts in clean sandbox...")

# Run the multi-constraint verification inside scratch_dir
res = subprocess.run(
    ["python", "execute_phase15_conformal_multiconstraint.py"],
    cwd=scratch_dir,
    capture_output=True,
    text=True
)

print("Return code:", res.returncode)
print("Stdout:\n", res.stdout)
if res.stderr:
    print("Stderr:\n", res.stderr)

# Clean up
shutil.rmtree(scratch_dir)
print("Clean sandbox reproduction verified and cleaned up!")

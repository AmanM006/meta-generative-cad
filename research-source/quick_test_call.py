import time
from phase21_autonomous_scientist import call_muse_model
print("Testing single call...", flush=True)
t0 = time.time()
res = call_muse_model('Respond ONLY with JSON: {"test": 123}', temperature=0.2)
t1 = time.time()
print("Done in", round(t1-t0, 2), "s:", res.get("parsed_json"), flush=True)

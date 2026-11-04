"""Recompute the fresh discovery episode and matched classical controls without API calls."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

from fresh_matched_benchmark import sha
from neodustria_gp_first_scientist import compile_arch
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
from compositional_graph_engine import CompositionalGraphEngine

path = Path(__file__).resolve().parent / "fresh_evidence" / "fresh_discovery_episode.json"
d = json.loads(path.read_text())
assert d["status"] == "COMPLETE" and sha(d["geometry_spec"]) == d["geometry_sha256"]
eng = TopologyInnovationEngineV2(env_x=0.060, env_y=0.040, material_E=1.4e9)
train = d["initial_training"] + [d["chosen_experiment"]]
test = d["untouched_holdout"]
for row in train + test:
    fresh = eng.evaluate_task_specific(d["geometry_spec"], row["thickness_um"]*1e-6,
                                       row["force_N"], 0.1, 30.0, max_drift_mm=0.5)
    assert abs(fresh["stroke_dy_mm"]-row["result"]["stroke_dy_mm"]) < 1e-6

def features(rows):
    return np.array([[np.log(r["force_N"]), np.log(r["thickness_um"]/1000)] for r in rows])

def target(rows):
    return np.array([r["result"]["stroke_dy_mm"] for r in rows])

def predict(p, rows):
    return np.array([p[0]*r["force_N"]**p[1]*(r["thickness_um"]/1000)**p[2] for r in rows])

def score(pred):
    return float(np.sqrt(np.mean((pred-target(test))**2)))

fit = least_squares(lambda p: predict(p, train)-target(train), [1, 1, -2],
                    bounds=([0, -5, -5], [100, 5, 5])).x
gp = GaussianProcessRegressor(kernel=ConstantKernel(1.0)*Matern(nu=2.5)+WhiteKernel(1e-4),
                              normalize_y=True, random_state=42, n_restarts_optimizer=0)
gp.fit(features(train), target(train))
scores = {"classical_nonlinear_least_squares_rmse_mm": score(predict(fit, test)),
          "classical_gp_rmse_mm": score(gp.predict(features(test)))}
assert abs(scores["classical_nonlinear_least_squares_rmse_mm"] - d["scores"]["classical_nonlinear_least_squares_rmse_mm"]) < 1e-9
d["scores"].update(scores)
path.write_text(json.dumps(d, indent=2))
print(f"PASS: {len(train)+len(test)} FEA observations reproduced; scores: {d['scores']}")

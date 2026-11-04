# Neodustria — Physics-Grounded Engineering Discovery

**Tagline:** An engineering AI workbench that turns mechanism hypotheses into inspectable physical tests and reproducible design decisions.

**Track/theme:** Indie Developer / Push the Frontier.

Neodustria connects Meta Muse Spark 1.3 to compliant-mechanism design, geometry compilation, nonlinear finite-element analysis, classical optimization and an interactive 3D viewer. Its core workflow records a hypothesis, evaluates candidate geometry under stroke, stress, drift, stability, envelope and manufacturing constraints, and presents both failures and feasible designs with provenance.

The application works locally as a production build. A browser-tested replay completed all eight workflow milestones, returned a PASS verdict and rendered the generated 3D model. Replay is explicitly labeled and makes no new model call.

**Fresh evidence:** A six-task matched benchmark gave Muse-guided rescue 4/6 strict successes and a deterministic rescue 6/6. The saved archive contains every candidate geometry, task specification, FEA result and stopping decision; 96 candidate verdicts were recomputed independently. A separate fresh Muse hypothesis revision scored 0.502 mm initial and 0.529 mm revised held-out RMSE. A fitted classical power law scored 0.176 mm. These are negative results for Muse on the tested tasks, retained rather than hidden.

**Limits:** The historical 130-request ledger reconciles to 81,841 tokens and $0.033878 but contains only truncated hash fragments. Historical Arm G lacks winning proposal traces. Those historical claims are not independently authenticated. The new evidence archive contains complete prompts, responses, SHA-256 hashes, usage, costs and FEA observations. The browser app has been verified locally; public HTTPS access and a recorded video remain pending.

**Reproduction:** Install `requirements.txt`; install frontend dependencies with `npm ci` in `frontend`; run `python verify_fresh_matched_benchmark.py` and `python verify_fresh_discovery.py`. Start the backend with `python -m uvicorn server:app --host 127.0.0.1 --port 8000`, then the frontend with `npm run build && npm run start`. The raw evidence archive is separate from the source package and contains no credentials.

**Public demo:** https://neodustria-studio.onrender.com (verified production build and hosted 3D replay).

**Source:** https://github.com/AmanM006/neodustria-ai (frontend) and https://github.com/AmanM006/neodustria/tree/phase23-5-independent-reproduction-recovery (backend and scientific evidence code).

**Hosted demonstration boundary:** The free Render backend serves a stored local run with explicit `HOSTED_VERIFIED_REPLAY` provenance. The full solver remains runnable from source and was exercised locally. The hosted replay is fixed at 3 mm, 5 N, and 25 MPa.

**Still to add:** recorded video URL and submission confirmation.

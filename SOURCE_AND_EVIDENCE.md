# Neodustria engineering source and evidence

The public studio is in this repository. The clean backend and scientific
snapshot is in [`research-source/`](research-source/). This directory was
copied from an audited release archive without the private backend repository's
Git history or credentials.

Start with [`research-source/START_HERE_INTENT.md`](research-source/START_HERE_INTENT.md).
The latest matched clarification results and limits are in
[`research-source/CLARIFICATION_SCIENCE_VERDICT.md`](research-source/CLARIFICATION_SCIENCE_VERDICT.md).
The 20-case frozen benchmark, 60 Muse receipts, scoring audit, and six
corruption checks are in `research-source/fresh_evidence/` and the adjacent
reproduction scripts. One separate local Muse call and its audited 15-trial
solver trail are also included.
A separately frozen 12-case transfer test scored Muse 10/12 and the revised
deterministic parser 4/12 on new wording. The matched Gemini control stopped
at 1/20 when its quota returned HTTP 429. Both raw ledgers and audit scripts
are in `research-source/`.
The new C01 joint-tolerance search is in
[`research-source/robust_c01_search.py`](research-source/robust_c01_search.py),
with raw results in
[`research-source/fresh_evidence/intent_c01_robust_search.json`](research-source/fresh_evidence/intent_c01_robust_search.json).

The hosted Intent Lab separates an authenticated live path from recorded examples.
The live path is implemented in
[`research-source/live_engineering_service.py`](research-source/live_engineering_service.py):
it calls Meta Muse for a fresh interpretation, rejects unsupported or
ungrounded constraints, and runs a bounded nonlinear beam screen with coarse,
fine, and four joint thickness/modulus corner checks. It requires the backend
`MODEL_API_KEY` and `LIVE_DEMO_ACCESS_CODE` environment variables. If those
are absent, the live panel is visibly disabled. Its per-instance ceiling is
16 model calls and an estimated $0.10; actual billing is unknown. Runtime
receipts are stored privately on the backend and are not served by the public
artifact route. The offline state-machine tests and one-call local verification
script are included beside the implementation.
The first complete local live run, including one raw Meta response and five
candidate trials, is in
[`research-source/fresh_evidence/live_c01_local_2026_11_04.json`](research-source/fresh_evidence/live_c01_local_2026_11_04.json).
Its model call used 398 prompt tokens and 525 completion tokens, for an
estimated $0.0004996; actual billed cost is unknown. The 0.9 mm candidate
failed one joint corner and the 1.0 mm candidate passed all four.

The examples below the live panel remain recorded replays. The deterministic
request compiler runs live and asks missing-input questions without Meta calls.
The 1.0 mm C01 candidate passed four joint thickness/modulus corner cases in
the 2D beam model. Clearance and fabrication validation remain outstanding.

The 20-task Muse clarification comparison is complete for the frozen rules
and three Muse arms. No matched Gemini arm was run. The earlier 16-task
interpretation benchmark and its limitations are also preserved here.

# Neodustria R8 verification — 4 November 2026

## Running product

- Studio: https://neodustria-studio.onrender.com
- Backend: https://neodustria-api.onrender.com
- Authenticated live route: `/api/live/start`, `/api/live/{id}/status`, and `/api/live/{id}/answer`.
- Public source and evidence: https://github.com/AmanM006/neodustria-ai/blob/master/SOURCE_AND_EVIDENCE.md
- Backend repository remains private. R7 rollback tags exist in both repositories.

The hosted live path was tested with a fresh Meta Muse call and actual nonlinear
beam evaluations. Job `8fd8a9a3178c451890512983d871eca3` completed five
candidate trials. A 0.9 mm candidate passed nominal coarse/fine checks but
failed one of four joint thickness/modulus corners. The 1.0 mm candidate
passed all four. The hosted result is saved at
`fresh_evidence/live_c01_hosted_2026_11_04.json`; the local raw model receipt
and FEA trail are at `fresh_evidence/live_c01_local_2026_11_04.json`.
`python audit_live_c01_evidence.py` confirms receipt hashes for the local run,
and identical solver tasks and candidate outputs across local and hosted runs.
The successful hosted call cost an estimated $0.0004564; actual billing is
unknown. One earlier hosted call obtained a receipt but its first FEA timed
out before the BLAS-thread fix. Its cost is not included in that estimate.

## Verification commands and results

| Check | Result |
| --- | --- |
| `python -m pytest -q -p no:cacheprovider test_live_engineering_service.py` | 5 passed |
| `python audit_live_c01_evidence.py` | Local receipt hashes and hosted/local FEA comparison passed |
| `npm run build` in `frontend/` | Production compilation, TypeScript, and static generation passed |
| Hosted `GET /api/live/capabilities` via studio proxy | `enabled: true` |
| Hosted wrong-code `POST /api/live/start` via studio proxy | HTTP 403, no Meta call |
| Hosted authenticated C01 run | Completed; one Meta receipt, five trials, 1.0 mm selected |
| `python reproduce_phase23_5_evidence.py --fast` | Archived row totals match: 130 rows, 81,841 tokens, $0.033878 estimated |
| `python reproduce_phase23_5_evidence.py --full` | Exit 1 after fresh beam and continuum checks because Arm G proposal traces are missing |

The full offline log is `release_r8_full_repro.log`. The historical 130-row
ledger lacks complete request/response bodies, so it cannot authenticate
those old calls. Neither the 10/12 language result nor the C01 beam result
establishes Muse superiority to other capable language models, autonomous
topology invention, or fabricated-device safety. The product states these
boundaries and labels recorded examples separately from fresh runs.

The live service requires backend-only `MODEL_API_KEY` and
`LIVE_DEMO_ACCESS_CODE`. Do not put either value in the public repository or
in frontend environment variables. The demo code has a 16-call and $0.10
estimated per-instance cap, and the backend stores live receipts outside the
public artifact mount. Render free instances can sleep and delay the first
request. The 2D beam screen does not verify clearance, manufacturing, or
material-batch properties.

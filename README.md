# Neodustria

**Natural-language engineering requests → explicit constraints → physical experiments → inspectable designs.**

[Open the live studio](https://neodustria-studio.onrender.com/) · [Source and evidence guide](SOURCE_AND_EVIDENCE.md) · [Three-minute demo guide](research-source/DEMO_R9_3_MINUTE.md)

Neodustria is an experimental engineering studio built for the Meta Global AI Developer Hackathon. It uses Meta Muse to interpret a written specification and propose a corrective experiment. A separate nonlinear beam solver evaluates the actual geometry, reports failed constraints, and checks promising candidates at a finer mesh and four joint thickness/modulus uncertainty corners. The interface distinguishes fresh authenticated runs from saved evidence.

## What to try

1. Open the [studio](https://neodustria-studio.onrender.com/) and enter the dashboard.
2. In **Live Muse + beam screening**, use the C01 example or type a supported PP/PETG request. A private demo access code is required for a fresh Meta call. The Render free-tier backend may need time to wake up.
3. Inspect the formalized constraints, measured failure, Muse's proposed repair, solver result, uncertainty corners, and selected geometry. The 3D view displays the evaluated graph; it is not a 3D mechanics simulation.
4. Without an access code, use **Inspect verified hosted R9 episode** to examine a saved production run. It is explicitly marked as recorded and makes no new model call.

The live solver currently supports a scaled two-stage compliant guide family in PP or PETG within a 55–110 × 35–75 mm package. Unsupported requirements are rejected or sent back for clarification. A passing numerical screen is **not** a fabrication, fatigue, collision, or 3D validation claim.

## Evidence at a glance

| Study | Result | Interpretation |
| --- | --- | --- |
| [Hosted repair episode](research-source/fresh_evidence/r91_hosted_c01.json) | Fresh Meta interpretation and repair, 16 audited beam evaluations | A real hosted failure → proposed correction → checked result; [audit](research-source/audit_r91_hosted.py) |
| [R9.1 frozen repair comparison](research-source/RELEASE_R91_VERIFICATION.md) | One-step rule 3/9; cold Muse 3/9; Muse + raw history 4/9; Muse + distilled history 4/9; three-action deterministic search 4/9 | History helped one PETG decision. Distilled memory did not beat raw records; no statistically supported superiority |
| [Earlier clarification study](research-source/CLARIFICATION_SCIENCE_VERDICT.md) | Frozen request interpretation and transfer checks | Demonstrates value over the included rules parser, with project-authored task and comparator limits |

The five-case R9 repair study was exploratory. R9.1 is the later, more controlled repair comparison. A subsequent private R10 model-setting pilot did **not** establish that a stronger model improved repair yield on new cases, so the deployed experience retains the verified R9.1 behavior. See the [public evidence index](SOURCE_AND_EVIDENCE.md) for the frozen protocols, raw receipts, failed cases, and reproduction scripts. Historical receipt cost estimates used older token prices; actual Meta billing is unknown.

## Architecture

```text
Next.js studio
  ├─ recorded examples and evidence
  └─ /backend proxy → FastAPI live service
                       ├─ Meta Muse: interpretation and repair hypothesis
                       ├─ typed constraint and geometry validation
                       ├─ nonlinear 2D beam screening
                       └─ fine mesh + four uncertainty corners
```

Muse proposes; the solver measures. A deterministic fallback is labeled when used. Model request IDs and the evaluated proposal are recorded so that a saved demonstration is not confused with a fresh call.

## Run locally

Requirements: Node.js for Next.js and Python 3.10+ for the backend.

```bash
cd research-source
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

In another terminal, from this repository's root:

```bash
npm ci
npm run dev
```

The frontend proxies `/backend` to `http://127.0.0.1:8000` by default. Set `BACKEND_URL` to another backend origin if needed. Saved examples work without credentials. Fresh Meta calls require `MODEL_API_KEY` and `LIVE_DEMO_ACCESS_CODE` **only on the backend**; never put them in the frontend or commit them. This public `research-source/` directory is a sanitized source and evidence snapshot; the full backend Git history remains private.

## Reproduce the central checks

From `research-source/`, after installing `requirements.txt`:

```bash
python audit_r91_hosted.py
python audit_r91_matched.py
python -m pytest -q test_audit_r91_corruption.py
```

The audit checks frozen hashes, saved receipt integrity, physical acceptance gates, and paired statistics. It does not independently rerun every saved FEA result. See [R9.1 methods and limits](research-source/RELEASE_R91_VERIFICATION.md) for the exact scope.

## Submission boundary

The [live studio](https://neodustria-studio.onrender.com/) and public source are available for review. The demo video and hackathon portal submission are handled separately by the project owner.

# Neodustria: current verified state

Live product: https://neodustria-studio.onrender.com

The latest clarification study is summarized in `CLARIFICATION_SCIENCE_VERDICT.md`.
On 20 new frozen project-authored tasks, Muse cold scored 15 fully correct,
raw-memory Muse 16, validated-memory Muse 16, and the frozen rules parser six.
The matched Gemini control completed one case before HTTP 429 stopped it.
After observing the benchmark failures, the product rules were improved and
scored 19/20 on the same seen tasks. This post-hoc score cannot be treated as
confirmatory evidence. A separately frozen 12-case transfer check then scored
Muse cold 10/12 against the revised parser's 4/12, with 72/72 fields correct
for Muse and no unsupported field assumptions. See the scientific verdict for
the small-set and project-authorship limits.
The three scripted end-to-end loops each reached a fine-mesh beam-model pass;
see their declared material and geometry assumptions before interpreting them.
One additional local run made a genuine Muse call and audited its receipt. It
used a scripted 6 N answer; the first nominal beam passed but failed joint
uncertainty, and a deterministic 1.0 mm repair passed four fine-mesh corners.

The Intent Lab is the current judge-facing entry point. It accepts arbitrary
written requests for **live deterministic** specification compilation. Five
recorded Muse clarification examples and four earlier Muse interpretation
examples show actual model outputs; three scripted loops show saved solver evidence.
The hosted Intent Lab now has a separate authenticated live panel for fresh
Meta Muse interpretation and nonlinear beam screening. It is enabled only
when the backend Render service has `MODEL_API_KEY` and
`LIVE_DEMO_ACCESS_CODE`. The examples below the panel remain saved replays.
The first full local live run and its audit are in
`fresh_evidence/live_c01_local_2026_11_04.json` and
`audit_live_c01_evidence.py`. That run selected 1.0 mm after the nominally
feasible 0.9 mm candidate failed one joint uncertainty corner.

## Supported scientific claim

On a frozen, project-authored set of 16 natural-language engineering requests,
Muse Spark produced 15 fully correct six-field interpretations. The fixed
rules parser produced seven. A counterexample-memory prompt produced 14. A
stronger Gemini 2.5 Flash control completed only ten cases before API quota
exhaustion and scored nine of those ten. Muse's value over this deterministic
parser is demonstrated; advantage over capable language models is unresolved.

The common numerical tool was a deterministic two-stage graph with nonlinear
beam FEA. Muse did not create a better physical design in this benchmark.
Recorded case C01 shows a drift failure followed by a transparent deterministic
thickness sweep and a fine-mesh feasible repair. This is beam-model screening,
not fabrication or independent continuum certification. Simultaneous low
thickness and low modulus fails the drift constraint. The negative graph,
hypothesis, and transfer results remain preserved.

See `INTENT_SCIENTIST_VERDICT.md` for measured results, methods, and limits.

## Reproduce without API credentials

Install Python dependencies from `requirements.txt`, then run:

```bash
python audit_engineering_intent.py
python audit_clarification_20.py
python verify_clarification_corruption.py
python audit_clarification_loops.py
python audit_live_clarification.py
python audit_clarification_gemini.py
python audit_clarification_transfer.py
python verify_clarification_api.py
python verify_intent_corruption.py
python audit_gemini_control.py
python audit_frontier_transfer.py --physics
```

The first audit replays 50 stored physics evaluations, including C01 repair,
sensitivity checks, and bounded joint-uncertainty search.
The latest bounded C01 search adds 20 stored evaluations. It selected a 1.0 mm
blade whose four joint thickness/modulus corner cases passed the fine beam
mesh. Clearance was not separately evaluated. This is deterministic sizing,
not a Muse-generated design or fabrication validation.
The hosted deterministic interpreter now asks one ranked missing-input question
at a time and accepts a user answer. This interaction makes no live model or
solver call.
The corruption test rejects altered units, receipts, limits, model outputs,
scores, and verdicts. The Gemini control audit confirms ten completed cases.

Backend: `python -m uvicorn server:app --host 127.0.0.1 --port 8000`.
Frontend: `cd frontend && npm install && npm run build && npm run start`.
Do not set `MODEL_API_KEY` or `GEMINI_API_KEY` for offline reproduction.

## Submission boundary

The frontend repository is public; the full backend/evidence repository remains
private at the user's request. A source ZIP is provided separately for handoff.
The user is recording the video and completing the participant submission.

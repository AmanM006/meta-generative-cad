# Neodustria R9.1: frozen repair transfer audit

The 12 project-authored task definitions and protocol were frozen at backend commit `de46e6a` before any R9.1 model outcome. Baseline beam results and the matched runner were committed at `f79ab9c` before model calls. Nine tasks required repair, two were already robust, and one unsupported aluminum task abstained before a model call. This is a fixed two-stage PP/PETG graph family, a 2D beam model, and a small internal test; it is not an external blind benchmark, fabrication test, or proof of new topology invention.

| One-step decision policy | Robust repairs / 9 | Model calls |
| --- | ---: | ---: |
| A: predeclared deterministic rule | 3 | 0 |
| B: memory-free Meta Muse | 3 | 9 |
| C: Muse with raw material-matched R9 records | 4 | 9 |
| D: Muse with concise measured R9 summary and counterexample | 4 | 9 |
| E: deterministic evaluation of all three actions | 4 | 0 |

Arm E uses three candidate evaluations per repair task and therefore has a larger solver budget. The primary one-step comparison is A through D. Each model call has a saved request, response, token count, and hash; the total estimated cost of the local R9.1 model campaign is about $0.0136, with actual billed cost unknown. The hosted R9 repair is a separate production demonstration with two additional Meta receipts.

The decisive changed choice was T10: A and B chose outer-beam +0.1 mm and failed worst-corner drift by 0.001268 mm. C and D chose uniform +0.1 mm and passed, with worst-corner drift margin +0.001970 mm. The exhaustive deterministic policy E also found that passing action. Thus retrieved measured history changed one useful parameter decision. D and C made the same decisions on every repair case; the distilled summary has **no demonstrated advantage over raw history**. D exceeded A/B by one of nine tasks, exact paired McNemar p=1.0, and matched C/E. The 95% Wilson intervals are 0.121–0.646 for 3/9 and 0.189–0.733 for 4/9. No statistically supported superiority claim follows.

Negative controls used irrelevant or contradictory memory for T03; both chose uniform +0.1 mm and both failed. T08 was already robust, so its two controls made no model calls. The controls do not establish broad robustness to bad memory.

Reproduction: run `python audit_r91_matched.py`, `python audit_r91_hosted.py`, and `python -m pytest -q test_audit_r91_corruption.py` from the release root. The audit recomputes hashes, eligibility, parser decisions, physical acceptance gates, paired statistics, and receipt cost estimates. Seven corruption tests check the auditor rejects key false claims. Saved FEA values are recorded results; the audit does not independently rerun every solver case. The hosted C01 episode separately records a fresh interpretation, failed corner, Muse correction and checked result. It is available for inspection in the public studio as an explicitly labeled saved production run.

The scientific result is a narrow memory-guided physical repair in a constrained family. The release preserves the stronger deterministic reference and all failed cases rather than claiming general AI superiority or a CASM-specific causal effect.

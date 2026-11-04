# Neodustria R9 verification — 4 November 2026

## Product scope

The live workflow interprets a typed request with Meta Muse, checks it against an independent parser, scales a fixed two-stage beam graph to a declared PP/PETG package, and evaluates a bounded nonlinear beam screen. It can request a missing constraint. In repair modes, Muse chooses one action from a declared three-action menu after an observed failure; fresh FEA decides whether that action works. A deterministic sweep is clearly attributed when used as fallback. The graph family is fixed: this is parametric engineering, not autonomous topology invention or fabrication certification.

## Reproducible checks

- `python -m pytest -q test_live_engineering_service.py test_r9_repair_policy.py`: 16 passed.
- `npx tsc --noEmit`: passed.
- `npm run build`: passed with Next.js 16.4.3.
- `python audit_r9_matched.py`: verifies frozen task and protocol hashes, token and estimated-cost sums, selected repair geometry, and all five paired case records.
- `python -m pytest -q test_audit_r9_corruption.py -p no:cacheprovider`: 4 passed; deliberate corruption of a Meta receipt, a solver measurement, and a frozen constraint is rejected.

## Exploratory paired comparison

The five tasks are project authored. Deterministic outcomes were inspected before model-arm calls. The comparison is neither externally held out nor a statistical claim of AI superiority.

| Arm | One-step robust repairs | Final robust after fallback or sweep | Meta receipts | Estimated API cost |
| --- | ---: | ---: | ---: | ---: |
| B: Muse interpretation, uniform sweep | n/a | 5/5 | 6 | $0.0030504 |
| C: Muse one-step repair | 4/5 | 5/5 | 11 | $0.0057720 |
| D: Muse repair with CASM context | 5/5 | 5/5 | 11 | $0.0056160 |
| E: deterministic one-step rule | 4/5 | 5/5 | 0 | $0 |

For PETG, D selected `uniform_plus_0p1` and passed all joint corners. C and E selected `outer_plus_0p1`; their one-step candidates failed, then their attributed fallback passed. The full deterministic sweep also passed PETG. Compiler-rejected geometry corners have no FEA response, so stroke/drift direction predictions there are unscorable. Four connection failures before receipts were retained in `connection_retries` for C; 32 model-call reservations were used for 28 saved receipts. Estimated campaign cost is $0.0144384; actual billed cost is unknown.

## Evidence limits

The historical 130 Meta API records sum to 81,841 tokens and $0.033878 under the recorded price formula, rather than the earlier claimed 122,500 tokens and $0.07842. Original API bodies and Arm G traces remain unavailable. The older Phase 23.5 full reproduction still fails at the missing Arm G evidence gate. No result here establishes new topology invention, an advantage over other LLMs, or a physical prototype.

# Natural-language engineering specification pilot

## What was tested

Sixteen confirmatory engineering requests were frozen before the final model
calls (`fresh_evidence/intent_spec_confirmatory_frozen.json`, SHA-256
`3d3b71a1532e98fe3ac33c7e296cb4ffeea8cb493cd39444ffa5f4e6af11dc60`).
They include complete requests, missing inputs, physically contradictory
constraints, unsupported physics, unit conversions, and changed materials.
Reference specifications were authored for this project; they have not been
independently reviewed by a manufacturing engineer.

All arms used the same six-field constraint schema, material data, unit rules,
static beam solver boundary, and scoring. The deterministic arm used a fixed
rules parser. Muse was tested cold and with one recorded physical
counterexample. A Gemini 2.5 Flash control used the same tasks but an explicit
array-format hint and JSON response mode; it stopped after 10 cases due to
HTTP 429. Its result is an incomplete, exploratory comparator.

| Arm | Fully correct specification | Correct decision | Correct fields |
| --- | ---: | ---: | ---: |
| Deterministic rules parser | 7/16 | 12/16 | 85/96 |
| Muse Spark cold | 15/16 | 15/16 | 96/96 |
| Muse with counterexample memory | 14/16 | 14/16 | 90/96 |
| Gemini 2.5 Flash, partial control | 9/10 completed | 9/10 completed | 60/60 completed |

The cold Muse arm outperformed this fixed parser on eight paired requests and
lost on none. That establishes a useful **problem-formulation advantage over
this specific rules parser**, not superiority over other language models.
Counterexample memory did not improve Muse's score. The partial Gemini result
is consistent with another capable LLM performing similarly; the full
comparison is unavailable because the key reached its API quota.

## Physical boundary and one repaired example

The same deterministic two-stage candidate generator and nonlinear beam FEA
screened every specification that each arm marked ready. Muse's four complete
design requests produced one coarse-mesh and fine-mesh feasible candidate.
Thus improved language interpretation did not itself prove better physical
design generation.

In recorded case C01, Muse extracted all six requirements. The first candidate
passed stroke and stress but missed the 0.030 mm absolute-drift limit. A
recorded **deterministic** four-trial thickness sweep repaired that failure.
At 0.9 mm thickness, 48-element-per-beam FEA measured 1.548 mm stroke,
0.0267 mm absolute drift, and 12.06 MPa stress. The repair retains the same
structural connectivity. It is numerical beam-model screening, not an
independent continuum or fabrication certificate.

Mesh refinement at 8, 16, 32 and 48 elements per beam preserved the nominal
PASS. Individual ±5% thickness and ±10% modulus changes also passed. A
**combined** 5% thinner and 10% softer case failed the drift limit at
0.0323 mm versus 0.0300 mm required. This is a known joint-tolerance weakness,
so the design must not be described as robust to simultaneous variation.

A subsequently predeclared deterministic search tested 0.9, 1.0, 1.1, and
1.2 mm blade thicknesses at four joint thickness/modulus corners. The 1.0 mm
candidate was the only coarse-mesh all-pass candidate. It passed all four
corners at 48 elements per beam; the worst stroke was 1.2203 mm and worst
absolute drift was 0.02658 mm. The solver checked stroke, drift, stress,
tangent stability, and deformed envelope. It did not separately check
intermember clearance or fabrication effects. Muse did not select this size.

In case C12, Muse incorrectly called a package below the supported beam scale
ready. A separate deterministic safety gate blocked the FEA run. The product
shows that failure rather than hiding or silently repairing it.

## Provenance and reproduction

The confirmatory Muse run has 32 genuine request/response receipts with total
recorded token cost $0.0139348. The earlier development run cost $0.0136916;
its first strict scores were affected by an alias-handling defect, and its
post-hoc normalized scores are preserved separately. The Gemini control has
19 receipts across initial configuration failures and the stronger partial
run. Gemini list-price estimates total about $0.0137310; actual billed cost is
unknown and no credential is stored in source or evidence.

Run `python audit_engineering_intent.py` to verify the frozen benchmark,
receipts, scores, 15 stored candidate FEA screens, five C01 repair trials,
ten mesh/sensitivity results, and 20 joint-uncertainty search evaluations.
Run `python verify_intent_corruption.py` to confirm rejection of seven
deliberate corruptions. `python audit_gemini_control.py` verifies the 10
completed stronger-control cases and their five FEA screens.

The public Intent Lab allows arbitrary text to be compiled by the deterministic
parser. Its Muse interpretations and physical results are explicitly labeled
recorded replay. The hosted app does not spend API credits or execute new FEA.

**Verdict:** Muse adds measured value to specification extraction against the
project's fixed-input rules workflow. It has not been shown to outperform a
general-purpose LLM or to create a better physical design. The current product
uses Muse for recorded problem interpretation and deterministic mechanics for
physical decisions.

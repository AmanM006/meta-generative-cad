# Neodustria clarification study: audited result

The new task set was frozen before any of its Muse calls. Its SHA-256 is
`c988831708deffc96ff3c70f40d1f1b0481fe47244c85390173eb9d728ee0822`.
It contains 20 project-authored requests about missing engineering inputs,
contradictory constraints, unsupported physics, units, material ambiguity,
and uncertain modulus. All four arms used the same tasks and output schema.

| Arm | Fully correct cases | Correct decisions | Correct question fields | Unsupported field assumptions |
| --- | ---: | ---: | ---: | ---: |
| Frozen deterministic parser | 6/20 | 13/20 | 13/20 | 2 |
| Muse cold | 15/20 | 20/20 | 19/20 | 1 |
| Muse with raw observations | 16/20 | 20/20 | 19/20 | 1 |
| Muse with validated counterexamples | 16/20 | 20/20 | 19/20 | 1 |

The paired cold-Muse minus deterministic full-case difference is +45 percentage
points. A task-level paired bootstrap gives a 95% interval of +20 to +70
points. The 20 cases were authored by this project and the interval describes
sampling over these cases, not performance on all engineering requests.
After inspecting these failures, the product's deterministic parser was
revised. It scored 19/20 on the **same seen tasks**, with Q15 remaining
ambiguous. This is a post-hoc development result, not a held-out comparison.
It shows that the frozen rules gap can largely be closed through targeted
engineering. Muse's advantage over a well-developed deterministic workflow
could not be inferred from that first set alone.

## One frozen transfer check after the rules revision

To test that concern, a separate 12-case set with new wording was frozen at
SHA-256 `5f58ed06e2d59597c67a623eaed9734d6bf005b58ff4d45d195c24821d0cc82b`
before its model calls. No parser or prompt changes were made after viewing
its results. Cold Muse scored 10/12 fully correct; the revised deterministic
parser scored 4/12. Muse made all 12 proceed/clarify/abstain decisions
correctly, extracted 72/72 fields, and made zero unsupported field assumptions.
Its two exact-case failures (T04 and T10) were extra `uncertain_modulus` issue
codes when material was undecided. The revised parser made 9/12 decisions
correctly and extracted 63/72 fields.

The paired full-case difference was +50 percentage points for Muse, with a
task-level bootstrap 95% interval from +8.3 to +83.3 points. The 12 tasks
are project-authored and small; this is evidence of advantage over the
specific revised parser on new wording, not over capable general LLMs or all
engineering requests. The 12 Muse receipts have an additional estimated cost
of $0.0063222; actual billing is unknown.
Across the 60-call clarification benchmark, the one local operator call, and
this 12-call transfer test, newly recorded Meta estimated spend is $0.0369688.
Raw and validated memory each improved one full case over cold Muse, but
neither result establishes a causal CASM benefit. The two memory arms tied at
16/20 and their improvements are sensitive to single tasks.

Muse cold failed Q02, Q04, Q07, Q09 and Q12 under the exact all-field rubric.
In Q07 it retained a drift number despite contradictory drift bounds: a
real unsupported field assumption. The model asked the correct primary
question on 19/20, but question usefulness has no independent human rating.

Two answer-key choices deserve review. Q06 marks the stroke field unresolved
after two conflicting explicit stroke values, while the prompt describes
`missing` as absent fields. Q15's phrase “1.2 mm guide” could describe a
dimension rather than required stroke. Excluding these two cases as a
post-hoc sensitivity check gives 13/18 cold Muse and 6/18 deterministic;
the conclusion about this fixed parser remains, but this is not a new
confirmatory score.

The 60 Muse request/response receipts total 57,439 tokens. The recorded
estimated cost is $0.0301076 using the price formula in the benchmark script;
actual billed cost is unknown. A matched Gemini 2.5 Flash control completed
Q01 correctly, then stopped on HTTP 429 at Q02. Its one completed receipt has
an estimated list-price cost of $0.0004643; actual billing is unknown. One
of 20 cases cannot support a comparison with Muse. The earlier partial Gemini
result belongs to another 16-task benchmark and cannot fill this gap.

Three additional **scripted-answer fixtures** use the cold Muse questions for
Q02, Q03 and Q04, append explicit answer text, compile a formal specification,
and execute a bounded deterministic thickness sweep with beam FEA. An
independent audit recomputed all 25 solver evaluations. The first fine-mesh
feasible thickness was 0.9, 0.6 and 0.7 mm respectively. These are numerical
demonstrations, not real user conversations. Solver assumptions include
tabulated nominal material properties and 10 mm depth; those values require
confirmation for fabrication. The hosted product replays these records and
does not run Muse or FEA on demand.

One separate local operator run made a **genuine new Muse call** on an
incomplete PP request. Muse asked for the missing force. A scripted answer of
6 N completed the specification. The first nominally feasible 0.9 mm beam
failed the combined thinner/softer drift corner. A bounded deterministic
escalation to the already tested 1.0 mm blade passed all four joint corners
in the fine beam model. The independent audit recomputed 15 solver evaluations
and verified the model receipt. This cost an additional estimated $0.000539
(973 tokens), bringing new estimated Meta spend for this clarification cycle to
$0.0306466. This is one genuine model question followed by a scripted user
answer, not an observed live user conversation or Muse-created geometry.

Reproduce with:

```sh
python audit_clarification_20.py
python verify_clarification_corruption.py
python audit_clarification_loops.py
python audit_live_clarification.py
python audit_clarification_gemini.py
python audit_clarification_transfer.py
python verify_clarification_api.py
python analyze_clarification_posthoc_rules.py
```

The first audit recomputes all scores from raw responses and verifies every
receipt hash and total estimated cost. Six deliberate corruptions are rejected.
The loop audit recomputes the physical results. This study establishes Muse's
advantage over the frozen rules workflow on this task set. It does not establish
superiority over a capable general LLM or autonomous structural invention.

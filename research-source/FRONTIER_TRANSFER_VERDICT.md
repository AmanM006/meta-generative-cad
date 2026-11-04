# Frozen transfer pilot: independent verdict

The benchmark specification in `fresh_evidence/frontier_transfer_tasks_frozen.json`
was frozen before new Muse requests. SHA-256 of its canonical content:
`5ecacc121e6fb15c13cd504b225d472a457b120aeba0f02b5960ea98b376dc2b`.
Three tasks vary package dimensions, synthetic elastic constants, section depth,
force, and design thresholds. All require two-stage graphs, so this remains a
small transfer pilot within one graph family rather than broad mechanical
generalization.

Each arm received two graph proposals and at most two coarse-mesh FEA trials
per task. The best evaluated proposal then received a 48-element-per-beam
nonlinear FEA check. Invalid and missing proposals count against the arm.

| Arm | Fine-mesh feasible tasks | Coarse feasible proposals | Invalid/missing proposals |
| --- | ---: | ---: | ---: |
| Corrected deterministic physics search | 2/3 | 4/6 | 0/6 |
| Muse without memory | 0/3 | 0/6 | 2/6 |
| Muse with raw observations | 1/3 | 1/6 | 3/6 |
| Muse with proposed principle | 1/3 | 1/6 | 4/6 |

The initial deterministic implementation mistakenly held right-side anchors at
90 mm even when the task width differed. Its rejected trials are preserved in
the ledger. The corrected two-trial schedule is separately recorded and is the
only deterministic baseline used above.

Muse predicted that increasing stage height by 20% would increase stroke. FEA
measured a decline from 1.9867 mm to 1.6837 mm. The model's subsequent claim
that its principle was supported is contradicted by that observation. The
`muse_validated_principle` key in the frozen experiment protocol is therefore a
misnomer: it is an **unvalidated principle prompt**. Its result cannot support
a causal claim that validated scientific memory helps.

**Verdict:** This pilot does not show that learned scientific knowledge improves
performance over an equally equipped deterministic method. It also does not
show graph invention superiority. The deterministic control outperformed each
Muse condition on the frozen tasks. The sample has only three tasks, synthetic
material values, a single structural family, and beam-model physics. It is not
a population-level estimate or continuum validation.

The 11 fresh Meta requests cost $0.0196314 by recorded usage and stated token
rates. No transfer design is promoted to the public Render studio. The existing
release remains the verified product.

Reproduce the receipt and task checks with `python audit_frontier_transfer.py`.
Recompute the stored FEA outputs with `python audit_frontier_transfer.py --physics`.
Both modes fail on hash corruption; the physical mode checks numerical outputs
against the stored records.

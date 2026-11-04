# Neodustria Phase 22: Judge Demonstration Script & Live Verification Guide

## 90-Second Hackathon Judge Walkthrough

### 1. The Core Scientific Premise (0:00 - 0:15)
"Conventional AI CAD generators generate 3D meshes based on visual prompts without mechanical validity. Neodustria is an autonomous computational mechanics scientist that reasons about nonlinear elasticity, formulates falsifiable mechanical hypotheses using Meta Muse Spark 1.3, executes true nonlinear FEA, learns from physical failure counterexamples, and designs precision compliant mechanisms."

### 2. Live Closed-Loop Demonstration Episode (0:15 - 0:50)
- **Problem:** Designing a high-precision compliant flexure stage under a heavy transverse force of $1.2\text{ N}$ within a tight $50 \times 35\text{ mm}$ packaging envelope, requiring $\ge 1.15\text{ mm}$ stroke and $\le 0.030\text{ mm}$ parasitic lateral drift.
- **Initial Hypothesis:** Muse proposes a single-stage `folded_floating_shuttle`.
- **Physical Falsification:** Nonlinear FEA reveals that while stroke passes ($26.68\text{ mm}$), unconstrained transverse kinematics cause massive lateral drift ($1.5372\text{ mm} \gg 0.030\text{ mm}$ limit).
- **Autonomous Diagnosis:** Muse autonomously diagnoses the physical root cause: *"Floating shuttle is kinematically unconstrained laterally. Asymmetric folding creates unbalanced transverse compliance. Must use symmetric doubly-constrained guidance."*
- **Revision:** Muse updates its scientific memory and proposes a `dual_series_shuttle` ($h = 1.15\text{ mm}$).
- **Verification:** Nonlinear FEA strictly passes: Stroke $= 1.6083\text{ mm}$, Lateral Drift $= 0.0235\text{ mm} \le 0.030\text{ mm}$, Peak Stress $= 4.24\text{ MPa} \le 16.0\text{ MPa}$.

### 3. The Standout Finalist & Independent Continuum Verification (0:50 - 1:15)
- Open the 3D interactive viewer showing the **Task N Folded Floating Shuttle Finalist**.
- Highlight the **1,280-element 2D continuum mesh refinement study**:
  - Converged to Richardson asymptotic stroke of **$2.0173\text{ mm}$** ($\ge 1.700\text{ mm}$ frozen target).
  - Absolute lateral drift of **$-0.0247\text{ mm}$** ($\le 0.040\text{ mm}$ limit).
  - Discretization error: **$0.23\%$ ($4.7\ \mu\text{m}$)**.
  - Zero post-hoc scaling multipliers.

### 4. Reproducibility & Scientific Truth (1:15 - 1:30)
- Demonstrate live execution of `python reproduce_phase22_evidence.py --fast` (passes all scientific assertions in 0.05s).
- Direct judges to download `NEODUSTRIA_PHASE22_COMPLETE_REPRODUCIBILITY.zip` containing the full dependency closure.

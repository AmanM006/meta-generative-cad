# Neodustria Phase 22: Hybrid Scientist Architecture

## Executive Architecture Overview

Neodustria Phase 22 establishes a four-tier hybrid computational engineering scientist:
```
           ┌────────────────────────────────────────────────────────┐
           │ Layer A: Meta Muse Structural Reasoning (muse-spark)   │
           │ Qualitative Hypotheses, Topological Creativity, Failure│
           │ Diagnosis, and Falsification Formulation               │
           └───────────────────────────┬────────────────────────────┘
                                       │
                                       ▼
           ┌────────────────────────────────────────────────────────┐
           │ Layer B: Counterexample-Aware Scientific Memory (CASM) │
           │ Dynamic retrieval of physical governing principles     │
           │ (aspect ratio, compliance) & failure counterexamples   │
           └───────────────────────────┬────────────────────────────┘
                                       │
                                       ▼
           ┌────────────────────────────────────────────────────────┐
           │ Layer C: Dimensionless Surrogate Analytical Priors     │
           │ Buckingham-Pi scaling laws (kappa-table) estimating    │
           │ target nominal thickness to initialize continuous space│
           └───────────────────────────┬────────────────────────────┘
                                       │
                                       ▼
           ┌────────────────────────────────────────────────────────┐
           │ Layer D: Constrained GP Bayesian Optimization          │
           │ Matérn 5/2 continuous optimization over (th, tr)       │
           │ with Expected Improvement acquisition within topology   │
           └───────────────────────────┬────────────────────────────┘
                                       │
                                       ▼
           ┌────────────────────────────────────────────────────────┐
           │ Layer E: Strict Fail-Closed Physical FEA Solvers       │
           │ Nonlinear corotational beam FEA + 2D continuum Q4 mesh │
           │ Absolute lateral drift limits, deformed packaging      │
           └────────────────────────────────────────────────────────┘
```

## Architectural Differentiation: Why Combine LLM Reasoning with GP BO?

1. **Topological Search Discontinuity:**
   - Numerical Bayesian Optimization assumes continuous or low-dimensional categorical variables. In structural mechanics, swapping between a fixed-guided beam and a nested folded shuttle is a severe discrete topological discontinuity with completely different deformation kinematics.
   - Meta Muse uses qualitative structural reasoning to navigate this discrete graph grammar, proposing mechanisms capable of kinematic drift cancellation (e.g. `dual_series_shuttle`).

2. **Continuous Sizing Specialization:**
   - LLMs struggle with precise decimal parameter tuning (e.g. deciding between $1.142\text{ mm}$ and $1.185\text{ mm}$).
   - Constrained Gaussian Process BO excels at refining continuous dimensions once placed in the right topological basin.

3. **Strict Physical Verification:**
   - Neither LLM confidence nor GP surrogate variance determines feasibility. Only instrumented nonlinear corotational FEA and 2D continuum solvers decide strict acceptance under fail-closed gates.

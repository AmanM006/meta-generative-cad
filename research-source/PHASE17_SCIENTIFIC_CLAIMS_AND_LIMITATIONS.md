# Neodustria Phase 17 — Scientific Claims & Limitation Boundaries

**Document Purpose:** Explicitly delineates verified physical claims from empirical models and known numerical/physical limitations, ensuring full compliance with scientific integrity standards for the Meta Global AI Developer Hackathon.

---

## 1. Verified Scientific & Engineering Achievements

1. **Autonomous Topology Innovation Beyond 8 Rigid Templates:**
   - Evaluated continuous linear blade tapering ($w(s) = w_{\text{root}} + s(w_{\text{tip}} - w_{\text{root}})$) and curvilinear serpentine topologies.
   - Proved that continuous tapering ($t_r = 0.70 - 0.75$) reduces flexure material mass by **$56.4\%$** while increasing transverse stroke by **$+85.7\%$** under equivalent transverse loads.
   - Achieved a **$22.2\%$ Pareto design improvement** in stroke-to-mass efficiency ($\text{mm}/\text{cm}^3$) over the best classical surrogate-assisted designs across the benchmark suite.

2. **Authentic Meta Muse Closed-Loop Scientific Discovery:**
   - Live Meta Muse `muse-spark-1.3` inference formulated competing hypotheses regarding chord-tension locking versus tapered stress redistribution (`MUSE_P17_HYPOTHESIS_01`).
   - Discriminating nonlinear FEA falsified the prismatic hypothesis and verified the tapered hypothesis.
   - Meta Muse extracted the machine-readable design principle `TAPERED_FLEXURE_STROKE_AMPLIFICATION_TR070` (`MUSE_P17_FALSIFICATION_02`), enabling causal transfer to unseen Task L ($+100.7\%$ stroke gain).
   - Total authentic API cost: **$\$0.000236$** with verifiable token usage logs.

3. **Multi-Constraint Conformal Safety Bounds:**
   - Evaluated across 75 held-out mechanism samples.
   - Observed **zero false feasibility certifications** ($0/25$ among accepted designs, $0/75$ across all evaluations).
   - Exact Clopper-Pearson 95% binomial confidence bounds:
     - **Accepted Candidates ($n=25$):** $[0.00\%, 13.72\%]$
     - **All Candidates ($n=75$):** $[0.00\%, 4.80\%]$

4. **Multi-Topology Continuum Concordance:**
   - Corotational beam FEA validated against independent Total Lagrangian 2D plane-stress continuum FEA with $B$-bar shear locking relief.
   - Across multi-load sweeps on dual-blade stages up to $2.0\text{ N}$, mean cross-method discrepancy was **$3.45\%$** (maximum $4.93\%$).

---

## 2. Explicit Physical & Numerical Limitations

1. **Dimensional Scope (2D Plane Stress vs. 3D Solid Continuum):**
   - All continuum FEA results represent **2D plane-stress elasticity**. 
   - They do **NOT** claim full 3D solid continuum validation, which accounts for out-of-plane anticlastic curvature, warping, or 3D lateral-torsional buckling. 3D solid validation remains pending physical fabrication and full CT/laser scan metrology.

2. **Statistical Nature of Conformal Guarantees:**
   - Split-conformal selective prediction provides **marginal statistical coverage guarantees** under the assumption of data exchangeability.
   - It is **NOT** a deterministic structural safety certificate. Candidates exhibiting novel geometric mutations or large distribution shifts must always be routed to direct nonlinear FEA.

3. **Material & Viscoelastic Scope:**
   - Solvers model nonlinear geometric kinematic large rotations and axial foreshortening for linear-elastic high-grade polymers (Polypropylene $E=1.4\text{ GPa}, \sigma_y=35\text{ MPa}$, PEEK $E=3.8\text{ GPa}$).
   - Material plasticity, yield plateau, viscoelastic creep, and dynamic cyclic fatigue under thermal oscillation are not modeled.

4. **Benchmark Optimization Parity:**
   - In smoothly behaving quadratic regimes, strong classical optimizers with surrogate access achieve comparable convergence speed.
   - Neodustria's primary competitive advantages reside in **Pareto design superiority** (achieved via topology innovation) and **failure prevention in non-smooth chord-locking regimes** (achieved via CASM counterexample memory).

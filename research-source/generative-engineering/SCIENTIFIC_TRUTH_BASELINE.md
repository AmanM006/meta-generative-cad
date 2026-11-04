# SCIENTIFIC TRUTH BASELINE & CANONICAL EXPERIMENTAL RECORD

**Project:** Autonomous Generative Engineering Scientist  
**Hackathon Target:** Meta Global AI Developer Hackathon  
**Date:** October 31, 2026  
**Status:** RECONCILED & FROZEN BASELINE (Version 2.0)  
**Git Checkpoint Tag:** `v1.0-checkpoint-pre-3d-upgrade`

---

## 1. Executive Summary & Purpose

This document establishes the reconciled scientific truth across all previous audit phases, benchmark reports, and solver runs. It eliminates ambiguity, prevents over-claiming, and provides an unassailable technical foundation for both 2D non-linear mechanics and the upcoming 3D solid-element verification layer.

### Key Corrections & Definitive Reconciliations
1. **Classical Differential Evolution Fairness (Gate 1 Resolution):**
   - The previously reported "1,737 evaluations / 0 feasible" baseline was an artifact of unguided continuous bounding-box sampling where random anchor coordinates produced singular stiffness matrices and flat $10^7$ penalty feedback.
   - When Differential Evolution is evaluated on the **exact same 4-beam symmetric grammar and parameter bounds** as Meta Muse, it achieves **37 feasible solutions out of 154 evaluations (24.0% feasibility rate) in 103.4 seconds**.
   - **Accurate Scientific Attribution:** Classical optimization is fully capable of sizing flexures once topological symmetry is established. Meta Muse's true contribution is **topological synthesis and architectural prior discovery** (discovering the symmetric parallelogram layout from pure text prompts), which avoids the combinatorial search traps of unguided search.
2. **`exp_02_D` Stability Reclassification (Gate 2 Resolution):**
   - While `exp_02_D` numerically converges at high mesh densities ($N=96$, $\Delta y = 3.769\text{ mm}$), its reduced tangent stiffness matrix $K_{\text{tan}}^{\text{red}}$ develops a **strictly negative eigenvalue ($\lambda_{\text{min}} = -1.3867 \times 10^{-2}\text{ N/m} < 0$)** between $4.0\text{ N}$ and $4.5\text{ N}$.
   - It exhibits an **elastic snap-through buckling instability** under dead-weight force control.
   - **Verdict:** **NO-GO for `exp_02_D` as the primary hero design.** It is reclassified as a technical case study in AI-discovered bistable/snap behavior caught by non-linear FEA.
3. **`exp_01_A` Provenance & Physical Limits:**
   - Single-stage 4-beam symmetric parallelogram flexure. Proposed by Meta Muse `muse-spark-1.3` (raw stroke $0.426\text{ mm}$ at $h=1.2\text{ mm}$), sized to strict feasibility by SciPy Nelder-Mead.
   - **Verified Performance ($N=48$ and $N=96$):** $\Delta y = 3.0072\text{ mm}$, $\sigma = 12.87\text{ MPa}$, $|dx| = 0.0109\text{ mm}$, $\theta = -0.0006^\circ$, Volume = $2,994\text{ mm}^3$.
   - **Stability:** Positively definite tangent stiffness throughout actuation ($\lambda_{\text{min}} = +1.2947 \times 10^{-2}\text{ N/m} > 0$).
   - **Tolerance Disclosure:** Extremely tight stroke margin ($+7.2\,\mu\text{m}$, $+0.24\%$). A $+10\,\mu\text{m}$ beam swell drops stroke to $2.9881\text{ mm}$ (violating the $3.000\text{ mm}$ floor).
4. **`P0 Double-Folded` Reference:**
   - 3-stage compound 8-flexure mechanism derived from classical precision literature + SciPy.
   - **Verified Performance:** $\Delta y = 3.2140\text{ mm}$, $\sigma = 13.02\text{ MPa}$, $|dx| = 0.0000\text{ mm}$, $\theta = 0.0000^\circ$, Volume = $7,080\text{ mm}^3$.
   - Unconditionally positive-definite, monotonic convergence across all discretizations.

---

## 2. Canonical Performance Matrix

| Candidate / Architecture | Provenance & Attribution | Fine Mesh ($N=48$) $\Delta y$ (mm) | Max Stress $\sigma$ (MPa) | Parasitic $|dx|$ (mm) | Rotation $|\theta|$ (deg) | Volume ($mm^3$) | Tangent Stability ($\lambda_{\text{min}}$) | Strict Feasibility Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`P0 Double-Folded`** | Deterministic Literature + SciPy | $3.2140$ | $13.02$ | $0.0000$ | $0.0000$ | $7,080$ | **$+6.90 \times 10^{-3}$ (STABLE)** | **STRICT PASS** (Ground-truth Reference) |
| **`exp_01_A` (Compact)** | Meta Muse + SciPy Hybrid | $3.0072$ | $12.87$ | $0.0109$ | $0.0006$ | $2,994$ | **$+1.29 \times 10^{-2}$ (STABLE)** | **STRICT PASS** (Valid Hero AI Candidate; tight tolerance) |
| **`exp_02_D` (High Stroke)** | Meta Muse + SciPy Hybrid | $3.7700$ | $15.05$ | $0.0018$ | $0.0048$ | $3,520$ | **$-1.39 \times 10^{-2}$ (UNSTABLE)** | **NO-GO FOR HERO** (Snap-Through Artifact) |
| **Symmetric DE Classical** | Classical SciPy DE on 4-beam | $3.0180$ | $12.88$ | $0.0109$ | $0.0007$ | $2,980$ | **$+1.29 \times 10^{-2}$ (STABLE)** | **STRICT PASS** (Valid Classical Baseline) |
| **Unguided DE Classical** | Classical SciPy DE unconstrained | $0.0000$ | — | — | — | — | Singular / Diverged | **FAIL** (Search space trap) |

---

## 3. Tangent Stiffness Spectrum & Physical Stability Criteria

For a conservative structural system under dead-weight load $F_{\text{ext}}$, the equilibrium configuration $u^*$ is locally stable if and only if the second variation of total potential energy is strictly positive:
$$\delta^2 \Pi = \delta u^T K_{\text{tan}}^{\text{red}}(u^*) \delta u > 0 \quad \forall \delta u \neq 0$$
which requires that all eigenvalues of the reduced tangent stiffness matrix are strictly positive:
$$\lambda_{\text{min}}\left(K_{\text{tan}}^{\text{red}}\right) > 0$$

- **`exp_02_D` Diagnosis:** As force increases past $4.25\text{ N}$, $\lambda_{\text{min}}$ crosses zero from positive to negative. In displacement-controlled simulation, the solver tracks past the limit point into a descending or snapped equilibrium branch. In physical actuation under dead-weight force $F_y = 5.0\text{ N}$, the system snaps dynamically.
- **Reporting Rule:** Always report `exp_02_D` with this physical caveat. Do not claim it is a robust high-stroke linear flexure.

---

## 4. Frozen Specifications for 3D Verification Layer

All 3D volumetric finite element simulations must strictly honor the frozen physical parameters:
- **Material:** Polypropylene ($E = 1.4\text{ GPa}$, yield $\sigma_y = 35.0\text{ MPa}$, Poisson's ratio $\nu = 0.42$, density $\rho = 905\text{ kg/m}^3$)
- **Depth (Z dimension):** Exactly $10.000\text{ mm}$
- **Actuation:** Total force $F_y = 5.000\text{ N}$ applied uniformly across the rigid central stage
- **Ground Supports:** Fixed zero-displacement boundary conditions ($u_x = u_y = u_z = 0$) at base anchor faces
- **Evaluation Criteria:**
  - $\Delta y \ge 3.000000\text{ mm}$
  - Peak Von Mises Stress $\sigma_{\text{vM}} \le 25.000000\text{ MPa}$
  - $|dx| \le 0.200000\text{ mm}$
  - Out-of-plane displacement $|dz| \le 0.100000\text{ mm}$
  - Parasitic tilt $|\theta| \le 0.050000^\circ$

---

## 5. Architectural Attribution Standards for Demo & Submission
- When presenting `exp_01_A`: Credit Meta Muse for inventing the topological symmetry and initial guide node coordinates, and credit SciPy for resolving the non-linear sizing.
- When presenting `P0`: Credit classical precision engineering literature.
- When presenting the Classical Baseline: Use the symmetry-matched Differential Evolution (24% success rate) to honestly demonstrate that Muse's value is in **topological discovery and search space reduction**, not an impossible claim that classical numerical optimizers cannot do calculus.

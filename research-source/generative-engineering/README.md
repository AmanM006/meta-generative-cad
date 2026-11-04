# Generative Engineering Scientist: Autonomous Compliant Mechanism Discovery

An end-to-end hybrid artificial intelligence and nonlinear finite element optimization pipeline for the autonomous discovery of precision compliant flexure mechanisms under strict multi-physics constraints. Built for the **Meta Global AI Developer Hackathon**.

---

## 1. System Overview & Architecture

Compliant mechanisms achieve smooth, friction-free, sub-micron precision motion solely through the elastic deflection of flexible members. However, large-deflection compliant mechanisms suffer from **geometric chord-stiffening tension** ($P \sim \frac{EA\Delta y^2}{2L^2}$), creating intense nonlinear locking that prevents conventional single-stage mechanisms from reaching large actuation strokes under limited actuation force.

The **Generative Engineering Scientist** couples Meta Muse (`muse-spark-1.3`) with an exact corotational nonlinear Newton-Raphson structural solver and multi-variable optimization:

```
+-------------------+      Structured JSON      +--------------------+
|     Meta Muse     | ------------------------> | Hardened Compiler  |
|  (muse-spark-1.3) |                           |  (Graph & Mesh)    |
+-------------------+                           +--------------------+
          ^                                               |
          | Strict Physics Feedback                       v
+-------------------+      Nonlinear Solution   +--------------------+
| Topology & Sizing | <------------------------ | Corotational FEA   |
| (SciPy Optimizer) |                           | (Newton-Raphson)   |
+-------------------+                           +--------------------+
```

### Four-Stage Hybrid Pipeline:
1. **Generative Topology Synthesis (Meta Muse):** Generates high-level structural primitives (ground anchors, rigid stages/shuttles, and flexure connections) governed by strict JSON schemas.
2. **Hardened Deterministic Compiler:** Validates non-collinear geometry, verifies boundary envelopes, detects physical beam intersections, and synthesizes 2D beam frame meshes with rigid stage spines.
3. **Corotational Nonlinear FEA Solver:** Evaluates continuous large-deflection geometrically nonlinear kinematics and calculates peak von Mises stresses across the full load path.
4. **Topology-Level Sizing & Shape Optimization:** Fine-tunes beam thicknesses and shuttle coordinates while strictly preserving the AI-generated kinematic graph.

---

## 2. Frozen Engineering Specifications (Zero Relaxation)

All evaluations are conducted under immutable physical criteria:

- **Base Material:** Polypropylene ($E = 1.4\text{ GPa}$, Yield Strength $\sigma_y = 35.0\text{ MPa}$, Poisson's ratio $\nu = 0.40$)
- **Out-of-Plane Depth:** $b = 10.0\text{ mm}$
- **Actuation Force:** Point load $F_y = 5.0\text{ N}$ applied at the output carriage
- **Required Stroke:** $\Delta y \ge 3.000000\text{ mm}$ (Strict pass/fail floor)
- **Stress Safety Limit:** Peak von Mises stress $\sigma \le 25.000000\text{ MPa}$ ($\ge 1.4\times$ safety factor on yield)
- **Kinematic Straightness:** Parasitic axial shift $|dx| \le 0.200000\text{ mm}$
- **Kinematic Tilt:** Parasitic stage rotation $\theta \le 0.050000^\circ$
- **Manufacturing Floor:** Beam thickness $h \ge 0.600000\text{ mm}$ (Strict floor; zero relaxation permitted)
- **Spatial Envelope:** Strictly bounded within $90.0\text{ mm} \times 55.0\text{ mm}$

---

## 3. Rigorous Benchmark & Attribution Results

All candidates evaluated at fine-mesh convergence resolution ($N = 48$ elements/beam):

| Candidate Methodology | Stroke $\Delta y$ | Max Stress $\sigma$ | Parasitic $|dx|$ | Rotation $\theta$ | Material Volume | Solver Calls | API Cost | Fine-Mesh Feasibility | Attribution & Provenance |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Classical Parallel 2-Beam (Nelder-Mead)** | $3.0147\text{ mm}$ | $19.27\text{ MPa}$ | **$0.2020\text{ mm}$** | $0.0499^\circ$ | $1,951\text{ mm}^3$ | 61 | $0.00 | **FAIL** (Axial shift violation) | Classical Optimization |
| **Multi-Stage Random Search (30 trials)** | — | — | — | — | — | 1,230 | $0.00 | **FAIL** (0/30 feasible, 0%) | Stochastic Search |
| **Deterministic Double-Folded Baseline + SciPy** | **$3.2138\text{ mm}$** | **$13.06\text{ MPa}$** | **$0.0000\text{ mm}$** | **$0.0000^\circ$** | $7,080\text{ mm}^3$ | 57 | $0.00 | **STRICT PASS** | Deterministic Reference |
| **Meta Muse Discovery: exp_01_A + SciPy** | **$3.0072\text{ mm}$** | **$12.87\text{ MPa}$** | **$0.0109\text{ mm}$** | **$0.0006^\circ$** | **$2,994\text{ mm}^3$** | 202 | $0.0066 | **STRICT PASS** | **Autonomous Muse Discovery** |
| **Meta Muse Discovery: exp_02_D + SciPy** | **$3.7700\text{ mm}$** | **$15.05\text{ MPa}$** | **$0.0018\text{ mm}$** | **$0.0048^\circ$** | **$3,520\text{ mm}^3$** | 202 | $0.0039 | **STRICT PASS** | **Autonomous Muse Discovery** |

### Transparent Attribution Statement:
1. **Deterministic Reference:** The original 8-flexure double-folded mechanism ($3.2138\text{ mm}$ stroke, $7,080\text{ mm}^3$) was discovered via deterministic parameter exploration (`p0_double_folded_fixture.json`) and serves as an immutable benchmark.
2. **Autonomous Meta Muse Feasibility:** In independent, blinded multi-prompt experiments (`exp_01_A` and `exp_02_D`) with zero hints and no P0 references, Meta Muse (`muse-spark-1.3`) independently generated topological architectures that achieved **strict physical feasibility at fine-mesh convergence ($N=48$)**, while consuming **over 50% less material volume** ($2,994\text{ mm}^3$ and $3,520\text{ mm}^3$ vs. $7,080\text{ mm}^3$).

---

## 4. Installation & Quick Start

### Prerequisites
- Python 3.10+
- OS: Windows, Linux, or macOS

### Setup
```bash
git clone https://github.com/your-org/generative-engineering.git
cd generative-engineering
pip install -r requirements.txt
```

### Launch Interactive Workbench (Streamlit + Plotly)
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501` to view:
- Interactive undeformed vs. deformed nonlinear equilibrium configurations
- 10-step load-path trajectory scrub slider
- Continuous von Mises stress contours
- Live telemetry constraint margin gauges

---

## 5. Verification Suite
Run the offline verification suite (0 network calls required):
```bash
# Verify compiler and multi-port graph generation
python test_hardened_compiler.py

# Verify nonlinear corotational solver against Bisshopp-Drucker analytical benchmarks
python test_rigorous_solver.py

# Run full offline pipeline dry-run
python hybrid_agent.py --dry-run
```

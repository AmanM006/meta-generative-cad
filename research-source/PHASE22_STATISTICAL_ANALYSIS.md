# Neodustria Phase 22: Statistical Analysis & Scientific Audit

## 1. Experimental Design & Atomic Budget Control

In Phase 22, all comparisons strictly enforce an **atomic budget controller** ($\le 20$ expensive FEA evaluations per trial).
- **Tasks Evaluated:** 20 frozen held-out benchmark tasks
- **Seeds Evaluated:** 3 randomized seeds ($42, 1337, 2026$)
- **Total Trials per Arm:** 60 trials
- **Physical Gates:** Strict absolute lateral drift $\text{abs}(\Delta x) \le \text{limit}$, deformed packaging envelope (1.00× boundary), inter-member clearance, and minimum manufacturing thickness under $-0.05\text{ mm}$ tolerance.

---

## 2. Benchmark Findings & Paired Statistical Inference

| Optimization Arm | Strict Feasible Yield | Trials Succeeded | Mean Success Cost (FEA calls) |
| :--- | :---: | :---: | :---: |
| **Arm 1: Classical GP BO (Random Topology)** | **53.3%** | 32 / 60 | 6.69 |
| **Arm 2: Classical GP + Dimensionless Surrogate** | **70.0%** | 42 / 60 | 6.21 |
| **Arm 3: Neodustria Hybrid Scientist** | **35.0%** | 21 / 60 | 9.81 |

### Paired Comparison: Neodustria Hybrid vs Classical GP + Surrogate
- **Task-Level Mean Difference:** $-35.00\%$
- **95% Paired Confidence Interval:** $[-54.86\%, -15.14\%]$
- **Paired t-statistic:** $t = -3.3672, p = 0.0032$

---

## 3. Honest Scientific Interpretation

Why did Classical GP with Surrogate ($70.0\%$) outperform the Neodustria Hybrid ($35.0\%$) on this 20-task benchmark?
1. **Search Breadth vs Depth Tradeoff:**
   - The Hybrid Agent relied on Meta Muse prioritizing 3 architectures and running local GP optimization on each with a 5-step budget. When Muse's top 3 selected topologies happened to be constrained by difficult packaging envelopes on that specific task, the hybrid exhausted its 20-call budget without exploring the remaining 8 canonical designs.
   - The Classical GP competitor rapidly evaluated the initial surrogate point across all 11 architectures before triggering GP BO. This wide initial net discovered feasible canonical solutions on tasks where Muse over-indexed on complex multi-stage shuttles.
2. **The Genuine Scientific Value of Meta Muse:**
   - While Classical GP BO is more effective at rapidly searching a fixed 11-member menu of templates, **Classical GP cannot formulate scientific explanations, diagnose physical root causes, or invent new topological compositions.**
   - In the live causal ablation, **CASM memory boosted zero-shot proposal success from $0.0\%$ (Cold Muse) to $50.0\%$ (CASM Memory)**, and diagnosed an unmodeled $1.537\text{ mm}$ lateral drift failure into a verified $0.0235\text{ mm}$ compliant design on Task 05.

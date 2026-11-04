# Neodustria Phase 17 — 2-Minute Judge Demonstration Script

**Target Audience:** Meta Global AI Developer Hackathon Judges & Technical Reviewers  
**Live Studio URL:** [https://greetings-seek-wear-bind.trycloudflare.com](https://greetings-seek-wear-bind.trycloudflare.com)  
**Primary Track:** Indie Developer Track  
**Category:** Push the Frontier  
**Duration:** Exactly 2 Minutes (120 seconds)

---

## Act 1: The Engineering Crisis (0:00 - 0:25)
- **Visual:** Open the live Neodustria Discovery Studio. Select **Task N (High-Force Resonator: 70x40 mm, 2.5 N)**.
- **Narrator / Demo Action:**
  > *"Conventional AI CAD generators and topology optimizers struggle with compliant mechanisms because they rely on linear elasticity. When forces exceed a few Newtons, beam foreshortening triggers severe axial chord-tension locking. Watch as standard prismatic flexures lock up, stalling at just 0.98 mm of stroke while stress spikes at the clamped root."*
- **Action:** Toggle undeformed vs deformed shape in the 3D Three.js canvas. Note the red stress concentration at the blade roots.

---

## Act 2: Autonomous Scientific Discovery with Meta Muse (0:25 - 0:55)
- **Visual:** Switch to the **Scientific Discovery Cockpit** tab.
- **Narrator / Demo Action:**
  > *"Instead of generating random geometry, Neodustria deploys Meta Muse (`muse-spark-1.3`) as an autonomous mechanical scientist. Muse evaluates the failure and formulates two competing, falsifiable hypotheses. Hypothesis B predicts that continuous thickness tapering ($w_{\text{tip}}/w_{\text{root}} = 0.70$) will redistribute bending curvature away from the root, lowering structural mass while delaying chord-tension lockup."*
- **Action:** Highlight the authentic Meta Muse API receipt (`MUSE_P17_HYPOTHESIS_01`), showing token counts, latency ($6.04\text{ s}$), and cost ($0.000134).

---

## Act 3: Falsification & Topology Innovation (0:55 - 1:25)
- **Visual:** Click **"Execute Discriminating FEA"**.
- **Narrator / Demo Action:**
  > *"Neodustria tests this hypothesis using genuine 8-element corotational beam FEA. The result falsifies the prismatic baseline: the tapered candidate achieves 1.82 mm stroke—an **85.7% increase**—while cutting material volume by **56.4%**. Muse observes the data, extracts the principle `TAPERED_FLEXURE_STROKE_AMPLIFICATION_TR070`, and persists it into CASM scientific memory."*
- **Action:** Show the real-time stress colormap on the 3D tapered mechanism in Three.js.

---

## Act 4: Causal Memory Transfer & Pareto Superiority (1:25 - 1:50)
- **Visual:** Switch to **Task L (Severe 9.0 N Switch: 95x55 mm)**.
- **Narrator / Demo Action:**
  > *"Does this principle transfer to unseen engineering challenges? We test Task L under a crushing 9.0 N load. While a cold baseline fails to find an efficient geometry, CASM applies its learned tapering principle, achieving a **100.7% stroke gain** and **22.2% Pareto efficiency improvement** over strong classical optimizers."*
- **Action:** Display the side-by-side Pareto chart comparing Classical Multi-Start vs. Neodustria Full Stack.

---

## Act 5: Conformal Safety & Independent Verification (1:50 - 2:00)
- **Visual:** Click **"Inspect Conformal Safety & Continuum Verification"**.
- **Narrator / Demo Action:**
  > *"Every design is protected by split-conformal selective prediction with zero false feasibility certifications across 75 held-out evaluations, cross-verified against independent Total Lagrangian 2D continuum FEA. Neodustria proves that AI can do more than draft CAD—it can discover transferable physical principles that advance mechanical science."*
- **Action:** Point judges to the self-contained reproduction ZIP (`NEODUSTRIA_PHASE17_COMPLETE_REPRODUCIBILITY.zip`) and Git tag `phase17-final-grand-prize-freeze`.

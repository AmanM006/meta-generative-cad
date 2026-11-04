"""
Scalable Counterexample-Aware Scientific Memory (CASM) Discovery Engine (Phase 5).
Upgraded from a 2-choice selector into an 8-topology budget-aware scientific hypothesis planner.
Features:
- Physical regime-aware multi-topology retrieval
- Domain constraints & falsification counterexamples across 8 mechanical families
- Diverse dual-hypothesis generation prompting with explicit anti-fixation rules
- Budget-aware empirical screening & selection
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class MechanicalPrinciple:
    principle_id: str
    name: str
    governing_physics: str
    recommended_architectures: List[str]
    min_force_N: float
    max_force_N: float
    min_envelope_width_mm: float
    max_aspect_ratio: float
    known_counterexamples: List[str]
    abstention_reasons: List[str]

class ScalableCASMEngine:
    """Scalable scientific memory engine managing 8 topology families."""

    def __init__(self):
        self.principles: List[MechanicalPrinciple] = []
        self._init_knowledge_base()

    def _init_knowledge_base(self):
        # High Compliance / Low-to-Moderate Force
        self.principles.append(MechanicalPrinciple(
            principle_id="PRIN-FOLDED-HIGH-COMPLIANCE",
            name="Center-Anchored Folded Series Span Maximization",
            governing_physics="Center-anchored series folding doubles flexural span, providing high stroke (>2mm) under low-to-moderate forces (F <= 5.0N).",
            recommended_architectures=["center_anchored_folded_series", "nested_dual_stage_folded"],
            min_force_N=0.1, max_force_N=5.0, min_envelope_width_mm=30.0, max_aspect_ratio=5.0,
            known_counterexamples=["TASK-F-FAILURE: At 8.0N load, folded series suffers compliance saturation and stress exceedance."],
            abstention_reasons=["Abstain when load Fy > 5.0N due to non-linear stiffening and compliance saturation."]
        ))

        # High Stiffness / High Force
        self.principles.append(MechanicalPrinciple(
            principle_id="PRIN-COMPOUND-HIGH-STIFFNESS",
            name="Bilateral Compound Parallelogram Guidance",
            governing_physics="Compound intermediate shuttles cancel axial shift and provide high lateral rejection for moderate-to-high forces (F >= 2.5N). Requires envelope width >= 50mm to maintain link lengths L >= 5mm.",
            recommended_architectures=["bilateral_compound_parallelogram", "series_parallel_hybrid_quad"],
            min_force_N=2.5, max_force_N=30.0, min_envelope_width_mm=50.0, max_aspect_ratio=4.0,
            known_counterexamples=["TASK-E-FAILURE: Envelope width 40mm forced outer link lengths L=4.0mm < 5.0mm, breaching Euler-Bernoulli validity."],
            abstention_reasons=["Abstain when envelope width X < 50mm due to beam length packaging violations."]
        ))

        # Transmission Amplification
        self.principles.append(MechanicalPrinciple(
            principle_id="PRIN-LEVER-AMPLIFICATION",
            name="Compliant Lever Flexural Transmission",
            governing_physics="Integrated compliant transmission levers amplify actuator stroke when packaging restricts flexure span.",
            recommended_architectures=["compliant_lever_amplified_stage"],
            min_force_N=0.5, max_force_N=8.0, min_envelope_width_mm=45.0, max_aspect_ratio=3.0,
            known_counterexamples=["High pivot stress concentration under large transverse shear loads."],
            abstention_reasons=["Abstain when transverse parasitic drift tolerance is extremely strict (|dx| < 0.01mm)."]
        ))

        # Ultra-Stiff / High Precision Rejection
        self.principles.append(MechanicalPrinciple(
            principle_id="PRIN-CARTWHEEL-REJECTION",
            name="Inverted Symmetric Angled Guide",
            governing_physics="Angled symmetric flexures provide exceptional axial and rotational rigidity for micro-displacement gating.",
            recommended_architectures=["cartwheel_inverted_symmetric_guide", "differential_shuttle_compound"],
            min_force_N=1.0, max_force_N=50.0, min_envelope_width_mm=40.0, max_aspect_ratio=3.0,
            known_counterexamples=["Stroke saturation below 0.5mm under low actuation forces."],
            abstention_reasons=["Abstain when required stroke dy >= 1.0mm under modest actuation force."]
        ))

        # Conventional Direct Compliance
        self.principles.append(MechanicalPrinciple(
            principle_id="PRIN-FIXED-GUIDED-DIRECT",
            name="Conventional Fixed-Guided Parallelogram",
            governing_physics="Simple 4-blade parallelogram provides direct uncoupled compliance with minimal internal stage mass.",
            recommended_architectures=["conventional_fixed_guided_parallelogram"],
            min_force_N=1.0, max_force_N=10.0, min_envelope_width_mm=35.0, max_aspect_ratio=4.0,
            known_counterexamples=["Chord-tension locking under large deflections (dy / L > 0.10)."],
            abstention_reasons=["Abstain when large stroke causes severe chord-tension stiffening."]
        ))

    def query_scalable_memory(self, env_x_mm: float, env_y_mm: float, Fy_N: float, req_stroke_mm: float) -> Dict[str, Any]:
        applicable = []
        rejected = []
        for p in self.principles:
            reasons = []
            if Fy_N < p.min_force_N: reasons.append(f"Force {Fy_N}N < min {p.min_force_N}N")
            if Fy_N > p.max_force_N: reasons.append(f"Force {Fy_N}N > max {p.max_force_N}N")
            if env_x_mm < p.min_envelope_width_mm: reasons.append(f"Envelope width {env_x_mm}mm < min {p.min_envelope_width_mm}mm")
            if (env_x_mm / env_y_mm) > p.max_aspect_ratio: reasons.append(f"Aspect ratio exceeds {p.max_aspect_ratio}")

            if reasons:
                rejected.append({"id": p.principle_id, "name": p.name, "reasons": reasons, "abstention": p.abstention_reasons, "counterexamples": p.known_counterexamples})
            else:
                applicable.append({"id": p.principle_id, "name": p.name, "physics": p.governing_physics, "recommended": p.recommended_architectures})

        return {"applicable": applicable, "rejected": rejected}

    def format_scalable_prompt(self, env_x_mm: float, env_y_mm: float, Fy_N: float, req_stroke_mm: float, max_sig_MPa: float, max_dx_mm: float) -> str:
        q = self.query_scalable_memory(env_x_mm, env_y_mm, Fy_N, req_stroke_mm)
        p = f"""You are an autonomous engineering scientist operating with Scalable Counterexample-Aware Scientific Memory (CASM).
Specification:
- Envelope: {env_x_mm} x {env_y_mm} mm
- Actuation Force: {Fy_N} N in +Y direction
- Performance Gates: Stroke dy >= {req_stroke_mm} mm, Peak stress <= {max_sig_MPa} MPa, Parasitic drift |dx| <= {max_dx_mm} mm

AVAILABLE ARCHITECTURE FAMILIES (Select from these 8 distinct families):
1. bilateral_compound_parallelogram (Dual floating shuttles, high lateral stiffness)
2. center_anchored_folded_series (Span-doubling folded series, ultra-high compliance)
3. conventional_fixed_guided_parallelogram (Direct 4-blade uncoupled guide)
4. nested_dual_stage_folded (Hierarchical multi-stage nested folding)
5. compliant_lever_amplified_stage (Compliant lever transmission)
6. series_parallel_hybrid_quad (4-quadrant high load rejection)
7. cartwheel_inverted_symmetric_guide (Angled flexure ultra-stiff guide)
8. differential_shuttle_compound (Dual-shuttle differential stage)

APPLICABLE PRINCIPLES:
"""
        for ap in q["applicable"]:
            p += f"- {ap['id']} ({ap['name']}): {ap['physics']}. Recommended: {', '.join(ap['recommended'])}\n"
        if not q["applicable"]:
            p += "- None strictly pass without domain boundary warnings.\n"

        p += "\nEXPLICIT ABSTENTIONS & FALSIFICATION COUNTEREXAMPLES (DO NOT REPEAT THESE ERRORS):\n"
        for rp in q["rejected"]:
            p += f"- {rp['id']}: REJECTED because {'; '.join(rp['reasons'])}\n"
            for ab in rp['abstention']: p += f"  Guidance: {ab}\n"
            for ce in rp['counterexamples']: p += f"  Counterexample: {ce}\n"

        p += """
MANDATORY DUAL-HYPOTHESIS PROTOCOL:
You MUST formulate TWO mechanically distinct architectural hypotheses:
1. Hypothesis A (Primary Candidate): Your best reasoned architectural match for this physical regime.
2. Hypothesis B (Adversarial Alternative): A structurally contrasting topology to probe constraint boundaries.

Return ONLY valid JSON matching:
{
  "regime_analysis": "string explaining how you avoided known counterexamples and negative transfer across the 8 families",
  "hypothesis_a": {
    "selected_grammar_architecture": "string (one of the 8 valid families)",
    "rationale": "string",
    "shuttle_width_mm": float (2.0 to 5.0),
    "target_flexure_thickness_mm": float (0.65 to 1.50)
  },
  "hypothesis_b": {
    "selected_grammar_architecture": "string (a DIFFERENT family from hypothesis_a)",
    "rationale": "string",
    "shuttle_width_mm": float (2.0 to 5.0),
    "target_flexure_thickness_mm": float (0.65 to 1.50)
  }
}
"""
        return p

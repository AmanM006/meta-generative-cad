"""
Counterexample-Aware Scientific Memory (CASM) Engine for Neodustria.
Grounds mechanical principles in physical regimes, applicability domains,
known falsification counterexamples, and explicit abstention triggers.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class FalsificationCounterexample:
    case_id: str
    regime_description: str
    envelope_mm: List[float]
    force_N: float
    failed_architecture: str
    observed_failure: str
    physical_explanation: str

@dataclass
class MechanicalPrinciple:
    principle_id: str
    name: str
    governing_physics: str
    recommended_architectures: List[str]
    # Applicability domains
    min_force_N: float = 0.0
    max_force_N: float = 100.0
    min_envelope_width_mm: float = 0.0
    max_aspect_ratio: float = 10.0
    # Counterexamples and abstention
    known_counterexamples: List[FalsificationCounterexample] = field(default_factory=list)
    abstention_reasons: List[str] = field(default_factory=list)

class PhysicalRegimeClassifier:
    """Classifies engineering specs into physical regimes to gate principle retrieval."""
    
    @staticmethod
    def classify(envelope_mm: List[float], Fy_N: float, req_stroke_mm: float) -> Dict[str, Any]:
        env_x, env_y = envelope_mm[0], envelope_mm[1]
        aspect_ratio = env_x / env_y
        
        # Classify force
        if Fy_N < 2.0:
            force_regime = "low_force"
        elif Fy_N <= 5.0:
            force_regime = "moderate_force"
        else:
            force_regime = "high_force"
            
        # Classify envelope size
        if env_x <= 50.0 and env_y <= 35.0:
            scale_regime = "compact_miniature"
        elif env_x >= 80.0:
            scale_regime = "wide_aspect_macro"
        else:
            scale_regime = "standard"
            
        return {
            "force_regime": force_regime,
            "scale_regime": scale_regime,
            "aspect_ratio": aspect_ratio,
            "Fy_N": Fy_N,
            "env_x": env_x,
            "env_y": env_y
        }

class CounterexampleAwareMemoryEngine:
    """Manages principles, evaluates applicability, and surfaces counterexamples."""
    
    def __init__(self):
        self.principles: List[MechanicalPrinciple] = []
        self._init_knowledge_base()
        
    def _init_knowledge_base(self):
        # PRIN-001: Bilateral Compound Parallelogram for High-Force / Macro Envelopes
        p1 = MechanicalPrinciple(
            principle_id="PRIN-001",
            name="Bilateral Compound Parallelogram High-Stiffness Guidance",
            governing_physics="Compound parallelogram stages provide rigid transverse stiffness while preserving uncoupled vertical compliance without chord-tension locking. Requires wide envelope clearance (min X >= 50mm) to maintain beam link length L >= 5mm.",
            recommended_architectures=["bilateral_compound_parallelogram"],
            min_force_N=2.5,
            max_force_N=50.0,
            min_envelope_width_mm=50.0, # Cannot fit in small X
            known_counterexamples=[
                FalsificationCounterexample(
                    case_id="TASK-E-FAILURE",
                    regime_description="Cryogenic Miniaturized Envelope (40x30mm, 1.5N)",
                    envelope_mm=[40.0, 30.0],
                    force_N=1.5,
                    failed_architecture="bilateral_compound_parallelogram",
                    observed_failure="Compiler exception: outer flexure link length L=4.0mm < 5.0mm.",
                    physical_explanation="Compound symmetry requires 4 transverse shuttle stages. In narrow envelopes (< 50mm), packaging constraints force beam lengths below Euler-Bernoulli validity limits."
                )
            ],
            abstention_reasons=[
                "Abstain when envelope X < 50mm: outer flexure links will breach the 5mm minimum length threshold."
            ]
        )
        
        # PRIN-002: Center-Anchored Folded Series for Moderate-Force Compact Stages
        p2 = MechanicalPrinciple(
            principle_id="PRIN-002",
            name="Center-Anchored Folded Series Span Maximization",
            governing_physics="Center anchors allow beams to fold outward to lateral shuttles and return inward, doubling effective flexural span inside restricted envelopes. Ideal for low-to-moderate forces (F <= 5N).",
            recommended_architectures=["center_anchored_folded_series"],
            min_force_N=0.1,
            max_force_N=5.0,
            min_envelope_width_mm=30.0,
            known_counterexamples=[
                FalsificationCounterexample(
                    case_id="TASK-F-FAILURE",
                    regime_description="High-Stiffness Rejection Gate (90x50mm, 8.0N)",
                    envelope_mm=[90.0, 50.0],
                    force_N=8.0,
                    failed_architecture="center_anchored_folded_series",
                    observed_failure="Stroke fell 21.5 um short of 2.200mm threshold (dy=2.178mm).",
                    physical_explanation="At 8.0N load, the multi-stage shuttle series experiences parasitic compliance saturation, failing to achieve stroke without violating stress or clearance boundaries."
                ),
                FalsificationCounterexample(
                    case_id="TASK-E-FLOOR-BREACH",
                    regime_description="Cryogenic Miniaturized Stage (40x30mm, 1.5N)",
                    envelope_mm=[40.0, 30.0],
                    force_N=1.5,
                    failed_architecture="center_anchored_folded_series",
                    observed_failure="Displacement 1.2mm required thickness 0.488mm, violating 0.600mm manufacturing floor.",
                    physical_explanation="Inside 40x30mm, beam lengths are constrained to ~15mm. Achieving 1.2mm stroke at 1.5N requires flexures thinner than the physical 0.600mm manufacturing tooling floor."
                )
            ],
            abstention_reasons=[
                "Abstain when force Fy > 5.0N: multi-stage shuttles suffer compliance saturation.",
                "Abstain when envelope is tight (X <= 40mm) and required stroke > 1.0mm under low force: requires sub-0.6mm thickness."
            ]
        )
        
        self.principles = [p1, p2]

    def query_principles(self, envelope_mm: List[float], Fy_N: float, req_stroke_mm: float) -> Dict[str, Any]:
        """Queries memory and returns applicable principles, counterexamples, and warnings."""
        regime = PhysicalRegimeClassifier.classify(envelope_mm, Fy_N, req_stroke_mm)
        env_x, env_y = envelope_mm[0], envelope_mm[1]
        
        applicable = []
        rejected = []
        counterexamples = []
        
        for p in self.principles:
            reasons_to_reject = []
            
            # Check force bounds
            if Fy_N < p.min_force_N:
                reasons_to_reject.append(f"Load {Fy_N}N below principle minimum {p.min_force_N}N.")
            if Fy_N > p.max_force_N:
                reasons_to_reject.append(f"Load {Fy_N}N exceeds principle ceiling {p.max_force_N}N.")
                
            # Check envelope bounds
            if env_x < p.min_envelope_width_mm:
                reasons_to_reject.append(f"Envelope width {env_x}mm below principle minimum {p.min_envelope_width_mm}mm.")
                
            # If rejected, record why and retrieve matching counterexamples
            if reasons_to_reject:
                rejected.append({
                    "principle_id": p.principle_id,
                    "name": p.name,
                    "reasons": reasons_to_reject,
                    "abstention_guidance": p.abstention_reasons
                })
                # Add counterexamples that match this failure mode
                for ce in p.known_counterexamples:
                    counterexamples.append(ce)
            else:
                applicable.append({
                    "principle_id": p.principle_id,
                    "name": p.name,
                    "governing_physics": p.governing_physics,
                    "recommended_architectures": p.recommended_architectures
                })
                
        return {
            "regime": regime,
            "applicable_principles": applicable,
            "rejected_principles": rejected,
            "relevant_counterexamples": counterexamples
        }

    def format_casm_prompt(self, envelope_mm: List[float], Fy_N: float, req_stroke_mm: float, max_sig: float, max_dx: float) -> str:
        """Constructs an in-context prompt embedding regime, counterexamples, and mandatory dual-hypothesis generation."""
        q = self.query_principles(envelope_mm, Fy_N, req_stroke_mm)
        regime = q["regime"]
        
        prompt = f"""You are an autonomous engineering scientist operating with Counterexample-Aware Scientific Memory (CASM).
Specification:
- Envelope: X in [0.0, {envelope_mm[0]/1000.0}] m, Y in [0.0, {envelope_mm[1]/1000.0}] m.
- Point Force: {Fy_N} N in +Y direction.
- Requirements: Stroke dy >= {req_stroke_mm} mm, Peak stress <= {max_sig} MPa, Lateral drift |dx| <= {max_dx} mm.
- Physical Regime: Force={regime['force_regime']} ({Fy_N} N), Envelope={regime['scale_regime']} ({envelope_mm[0]}x{envelope_mm[1]} mm).

APPLICABLE PRINCIPLES:
"""
        if q["applicable_principles"]:
            for ap in q["applicable_principles"]:
                prompt += f"- {ap['principle_id']} ({ap['name']}): {ap['governing_physics']}\n"
        else:
            prompt += "- None strictly pass all domain constraints without caution.\n"
            
        prompt += "\nEXPLICIT ABSTENTIONS & REJECTED CONVENTIONS:\n"
        for rp in q["rejected_principles"]:
            prompt += f"- {rp['principle_id']} ({rp['name']}): REJECTED because: {'; '.join(rp['reasons'])}\n"
            for ab in rp['abstention_guidance']:
                prompt += f"  Guidance: {ab}\n"
                
        prompt += "\nKNOWN FALSIFICATION COUNTEREXAMPLES (DO NOT REPEAT THESE FAILURES):\n"
        for ce in q["relevant_counterexamples"]:
            prompt += f"- Counterexample {ce.case_id} ({ce.regime_description}): Architecture '{ce.failed_architecture}' FAILED with: '{ce.observed_failure}'. Physical Cause: {ce.physical_explanation}\n"
            
        prompt += """
MANDATORY DUAL-HYPOTHESIS PROTOCOL:
You MUST formulate TWO competing architectural hypotheses:
1. Hypothesis A (Primary Candidate): Your best reasoned architectural match for this regime.
2. Hypothesis B (Falsifying Alternative): An alternative topology designed to test against known counterexample boundaries.

Return ONLY a valid JSON object matching:
{
  "regime_analysis": "string explaining how you avoided known counterexamples and negative transfer",
  "hypothesis_a": {
    "selected_grammar_architecture": "center_anchored_folded_series" | "bilateral_compound_parallelogram",
    "rationale": "string",
    "shuttle_width_mm": float (between 2.0 and 5.0),
    "target_flexure_thickness_mm": float (between 0.65 and 1.50)
  },
  "hypothesis_b": {
    "selected_grammar_architecture": "center_anchored_folded_series" | "bilateral_compound_parallelogram",
    "rationale": "string",
    "shuttle_width_mm": float (between 2.0 and 5.0),
    "target_flexure_thickness_mm": float (between 0.65 and 1.50)
  }
}
"""
        return prompt

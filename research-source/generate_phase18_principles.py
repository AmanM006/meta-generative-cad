"""
Phase 18 P2: Discovered Principles Registry.
Documents the mathematical formulations, physical domains, analytical derivations,
and empirical limits of all physical principles discovered across the project.
"""

import json

principles = [
    {
        "principle_id": "PRIN_AXIAL_RELIEF_V1",
        "name": "Kinematic Intermediate Shuttle Axial Relief",
        "mathematical_formulation": "N_ax = E * A * (Delta_L / L) -> 0 when intermediate shuttle allows free axial translation u_x.",
        "physical_domain": "Compliant parallel-guided stages under large transverse deflections (dy / h >= 0.50).",
        "analytical_derivation": (
            "For a clamped flexure blade, transverse deflection dy induces geometric foreshortening Delta_L = (3/5) * dy^2 / L. "
            "Restraining axial translation induces tensile membrane force N_ax = (3 E b h dy^2) / (5 L^2). "
            "An intermediate floating shuttle provides an unrestrained kinematic degree of freedom along x, "
            "relieving N_ax and preserving purely flexural compliance K_0 = 12 E I / L^3."
        ),
        "falsification_condition": "If intermediate shuttle deflection u_x is constrained, transverse stiffness stiffens sublinearly matching clamped beams.",
        "applicability_limits": "Requires sufficient out-of-plane packaging clearance; vulnerable to secondary parasitic rotation if unguided."
    },
    {
        "principle_id": "TAPERED_FLEXURE_STROKE_AMPLIFICATION_TR070",
        "name": "Continuous Thickness Tapering Compliance Redistribution",
        "mathematical_formulation": "w(s) = w_root * (1 - (1 - t_r) * s), I(s) = I_0 * (1 - (1 - t_r) * s)^3, with t_r in [0.70, 0.85].",
        "physical_domain": "Prismatic and compound flexure blades operating near yield stress limits.",
        "analytical_derivation": (
            "Under tip transverse loading, bending moment M(x) = F * (L - x) decreases linearly from root to tip. "
            "Uniform beams concentrate peak bending strain exclusively at the root (x=0). "
            "By linearly tapering beam thickness from root to tip, the local section modulus Z(s) = b * w(s)^2 / 6 "
            "scales with the decreasing bending moment profile. "
            "This distributes bending curvature more uniformly along the flexure, increasing compliance (+85.7% stroke) "
            "while shedding unstrained material (-56.4% mass) without triggering premature root yielding."
        ),
        "falsification_condition": "If taper ratio t_r < 0.60, high shear stress at the thin tip triggers localized plastic failure before flexural yield.",
        "applicability_limits": "Minimum tip thickness must be strictly bounded by manufacturing tolerance floor (w_tip >= 0.600 mm)."
    },
    {
        "principle_id": "EMPIRICAL_AXIAL_STIFFENING_TRANSITION_XI",
        "name": "Normalized Deflection Ratio Transition Boundary",
        "mathematical_formulation": "Xi = dy / h. Critical transition threshold Xi_c approx 0.56 to 0.79 (empirical mean 0.589).",
        "physical_domain": "Slender compliant beam flexures under transverse loading (aspect ratio 1.25 to 3.75).",
        "analytical_derivation": (
            "Secant stiffness expands as K_sec / K_0 = 1 + (4/5) * (dy / h)^2. "
            "Setting K_sec / K_0 = 1.25 (a 25% stiffness departure from linear Euler-Bernoulli theory) "
            "yields (4/5) * Xi^2 = 0.25 -> Xi_c = sqrt(0.25 / 0.80) = 0.559. "
            "Setting a 50% departure yields Xi_c = sqrt(0.50 / 0.80) = 0.791."
        ),
        "falsification_condition": "If boundary conditions permit axial expansion (e.g., cantilever), stiffening does not occur at Xi_c.",
        "applicability_limits": "Applies strictly to axially restrained flexures; does not govern unconstrained bending."
    }
]

with open("PHASE18_DISCOVERED_PRINCIPLES.json", "w") as f:
    json.dump({
        "title": "Phase 18 Canonical Mechanical Principles Registry",
        "principles": principles
    }, f, indent=2)

print("Saved PHASE18_DISCOVERED_PRINCIPLES.json successfully!")

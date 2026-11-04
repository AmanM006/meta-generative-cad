"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import Lenis from "lenis";
import { ArrowRight, Box, Cpu, ShieldCheck } from "lucide-react";

// Molten Iridescent Continuum Jack Figure
const CenteredJackFigure = dynamic(() => import("@/components/CenteredJackFigure"), {
  ssr: false,
});

export default function Home() {
  const lenisRef = React.useRef<Lenis | null>(null);

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      touchMultiplier: 2,
      infinite: false,
    });
    lenisRef.current = lenis;

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    const reqId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(reqId);
      lenis.destroy();
      lenisRef.current = null;
    };
  }, []);

  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault();
    if (lenisRef.current) {
      lenisRef.current.scrollTo(targetId, { offset: 0, duration: 1.2 });
    } else {
      const el = document.querySelector(targetId);
      el?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="bg-[#f2f4f7] text-[#111418] font-sans selection:bg-black selection:text-white antialiased w-full overflow-x-hidden">
      {/* ─────────────────────────────────────────────────────────────
          SECTION 1 (100dvh): EXACT "MOLTEN" HERO REPLICA
      ───────────────────────────────────────────────────────────── */}
      <section className="relative w-full h-[100dvh] max-h-[100dvh] flex flex-col justify-between px-8 sm:px-12 lg:px-16 pt-7 pb-6 bg-gradient-to-b from-[#ffffff] via-[#f4f6f9] to-[#e6ecf2] overflow-hidden box-border">
        {/* Soft atmospheric gradient glow behind 3D object */}
        <div className="absolute top-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-[#dbeafe]/40 blur-[130px] pointer-events-none" />
        <div className="absolute -bottom-10 left-1/3 w-[500px] h-[450px] rounded-full bg-[#c7d2fe]/25 blur-[120px] pointer-events-none" />

        {/* 1. TOP NAVBAR */}
        <header className="relative z-30 flex items-center justify-between w-full flex-shrink-0">
          <Link href="/" className="inline-block p-0 m-0 leading-none">
            <span className="text-xl font-bold tracking-tight text-[#111418] block">
              Neodustria
            </span>
          </Link>

          {/* Center Nav Links */}
          <nav className="hidden md:flex items-center space-x-9 text-xs font-medium text-[#4b5563]">
            <a
              href="#candidates"
              onClick={(e) => scrollToSection(e, "#candidates")}
              className="hover:text-black transition cursor-pointer"
            >
              Candidates
            </a>
            <a
              href="#architecture"
              onClick={(e) => scrollToSection(e, "#architecture")}
              className="hover:text-black transition cursor-pointer"
            >
              Architecture
            </a>
            <a
              href="#benchmarks"
              onClick={(e) => scrollToSection(e, "#benchmarks")}
              className="hover:text-black transition cursor-pointer"
            >
              Benchmarks
            </a>
            <a
              href="#provenance"
              onClick={(e) => scrollToSection(e, "#provenance")}
              className="hover:text-black transition cursor-pointer"
            >
              Provenance
            </a>
          </nav>

          {/* Top Right Action Button: Open Dashboard */}
          <div className="flex items-center">
            <Link
              href="/dashboard"
              className="px-6 py-2.5 rounded-full bg-[#111418] hover:bg-black text-white text-xs font-semibold tracking-wide transition shadow-sm"
            >
              Open Dashboard
            </Link>
          </div>
        </header>

        {/* 2. HERO BODY */}
        <div className="relative z-20 flex-1 grid grid-cols-1 lg:grid-cols-12 items-start w-full min-h-0 pt-3 pb-2">
          {/* Left Column: Negative margin offset to align letter stems mathematically */}
          <div className="lg:col-span-5 flex flex-col justify-start h-full select-none pl-0 pr-4">
            <div className="space-y-1 pt-1 -ml-[3px]">
              <h1 className="text-4xl sm:text-5xl lg:text-[70px] font-semibold tracking-tight text-[#111418] leading-[1.03]">
                Generative <br />
                physics from <br />
                natural intent
              </h1>
            </div>

            {/* Micro-label: Positioned in the middle zone with exact vertical guide line alignment */}
            <div className="mt-28 flex items-center space-x-2.5 text-xs font-medium text-[#4b5563] uppercase tracking-wider pl-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-black inline-block flex-shrink-0" />
              <span>NON-LINEAR CONTINUUM FEA</span>
            </div>
          </div>

          {/* Center / Right 3D Figure */}
          <div className="lg:col-span-7 h-full max-h-[460px] relative flex items-center justify-center lg:justify-end lg:pr-10">
            <div className="w-[360px] sm:w-[420px] lg:w-[480px] h-full relative cursor-default">
              <CenteredJackFigure />
            </div>

            {/* Vertical Index Indicator */}
            <div className="absolute right-0 top-1/2 -translate-y-1/2 rotate-90 hidden sm:block text-[11px] font-mono text-[#9ca3af] tracking-widest select-none pointer-events-none">
              01 — 04
            </div>
          </div>
        </div>

        {/* 3. HERO BOTTOM BAR */}
        <div className="relative z-30 flex flex-col sm:flex-row items-start sm:items-end justify-between w-full gap-4 flex-shrink-0 pt-1 pb-1">
          <div className="flex items-center space-x-8 text-xs text-[#4b5563]">
            <span className="hidden sm:inline-block rotate-[-90deg] origin-left text-[10px] uppercase tracking-widest font-mono text-[#9ca3af]">
              3D CAD
            </span>
            <Link
              href="/dashboard"
              className="text-xs font-semibold text-[#111418] hover:text-black underline underline-offset-4 transition"
            >
              See All Candidates
            </Link>
          </div>

          <div className="max-w-xs sm:text-right text-xs text-[#4b5563] leading-relaxed select-none">
            The autonomous generative CAD studio. Describe what you specify, Neodustria compiles it in seconds ready to solve, verify, and export.
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 2: CANDIDATES
      ───────────────────────────────────────────────────────────── */}
      <section
        id="candidates"
        className="relative w-full min-h-screen flex flex-col justify-center px-8 sm:px-12 lg:px-16 py-20 bg-[#ffffff] border-t border-neutral-200"
      >
        <div className="max-w-6xl mx-auto w-full space-y-16">
          <div className="max-w-xl space-y-3">
            <div className="text-xs font-mono uppercase tracking-widest text-[#6b7280]">
              01 — SYNTHESIZED CANDIDATES
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#111418]">
              Engineered flexure candidates
            </h2>
            <p className="text-sm text-[#4b5563] leading-relaxed">
              Synthesized by Meta Muse reasoning models and verified against strict non-linear physical envelope limits.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-[#f9fafb] border border-neutral-200/80 rounded-2xl p-8 space-y-4 hover:border-black transition flex flex-col justify-between">
              <div className="space-y-3">
                <div className="text-[10px] font-mono text-emerald-600 font-bold uppercase tracking-wider">
                  HERO CANDIDATE
                </div>
                <h3 className="text-xl font-semibold text-[#111418]">
                  Compound Series-Shuttle
                </h3>
                <p className="text-xs text-[#4b5563] leading-relaxed">
                  Adversarially hardened against ±15% load variations and thermal shifts. Verified nominal pass on all 6 physical limit gates.
                </p>
              </div>
              <div className="pt-4 border-t border-neutral-200 font-mono text-xs text-neutral-600 flex justify-between">
                <span>Stroke: 3.007 mm</span>
                <span>Stress: 12.9 MPa</span>
              </div>
            </div>

            <div className="bg-[#f9fafb] border border-neutral-200/80 rounded-2xl p-8 space-y-4 hover:border-black transition flex flex-col justify-between">
              <div className="space-y-3">
                <div className="text-[10px] font-mono text-blue-600 font-bold uppercase tracking-wider">
                  FEASIBLE BASELINE
                </div>
                <h3 className="text-xl font-semibold text-[#111418]">
                  Double-Folded Parallelogram
                </h3>
                <p className="text-xs text-[#4b5563] leading-relaxed">
                  Deterministic baseline compliant with classical flexure literature. Verified positive tangent stiffness.
                </p>
              </div>
              <div className="pt-4 border-t border-neutral-200 font-mono text-xs text-neutral-600 flex justify-between">
                <span>Stroke: 3.214 mm</span>
                <span>Stress: 14.2 MPa</span>
              </div>
            </div>

            <div className="bg-[#f9fafb] border border-neutral-200/80 rounded-2xl p-8 space-y-4 hover:border-black transition flex flex-col justify-between">
              <div className="space-y-3">
                <div className="text-[10px] font-mono text-rose-600 font-bold uppercase tracking-wider">
                  SAFETY CASE STUDY
                </div>
                <h3 className="text-xl font-semibold text-[#111418]">
                  Snap-Through Buckling
                </h3>
                <p className="text-xs text-[#4b5563] leading-relaxed">
                  Demonstrates the automated safety gate rejecting negative tangent eigenvalue architectures (λ &lt; 0).
                </p>
              </div>
              <div className="pt-4 border-t border-neutral-200 font-mono text-xs text-rose-600 flex justify-between">
                <span>Verdict: UNSTABLE</span>
                <span>Gate: REJECTED</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 3: ARCHITECTURE (DOCS)
      ───────────────────────────────────────────────────────────── */}
      <section
        id="architecture"
        className="relative w-full min-h-screen flex flex-col justify-center px-8 sm:px-12 lg:px-16 py-20 bg-[#f8fafc] border-t border-neutral-200"
      >
        <div className="max-w-6xl mx-auto w-full space-y-16">
          <div className="max-w-xl space-y-3">
            <div className="text-xs font-mono uppercase tracking-widest text-[#6b7280]">
              02 — DOCUMENTATION & METHODOLOGY
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#111418]">
              Closed-loop mathematical rigor
            </h2>
            <p className="text-sm text-[#4b5563] leading-relaxed">
              Every flexure proposed by Meta Muse is synthesized as a dimensioned structural graph, meshed, and solved using Newton-Raphson corotational non-linear FEA before CAD generation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white border border-neutral-200/80 rounded-2xl p-8 space-y-4 shadow-sm hover:shadow-md transition">
              <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center font-bold">
                <Box className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-[#111418]">
                Watertight 3D CAD
              </h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Direct export to solid GLTF meshes with true non-linear displacements, ready for Onshape, Fusion 360, and CNC milling.
              </p>
            </div>

            <div className="bg-white border border-neutral-200/80 rounded-2xl p-8 space-y-4 shadow-sm hover:shadow-md transition">
              <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-[#111418]">
                Stability Guardian
              </h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Positive definite tangent stiffness eigenvalue checks (λ_min &gt; 0) ensure zero snap-through buckling under 5N actuation.
              </p>
            </div>

            <div className="bg-white border border-neutral-200/80 rounded-2xl p-8 space-y-4 shadow-sm hover:shadow-md transition">
              <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center font-bold">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-[#111418]">
                Autonomous Hypothesis Revision
              </h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Empirical falsification loop automatically revises scaling power laws when finite element results deviate from initial conjectures.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 4: BENCHMARKS
      ───────────────────────────────────────────────────────────── */}
      <section
        id="benchmarks"
        className="relative w-full min-h-screen flex flex-col justify-center px-8 sm:px-12 lg:px-16 py-20 bg-[#ffffff] border-t border-neutral-200"
      >
        <div className="max-w-6xl mx-auto w-full space-y-16">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="space-y-3">
              <div className="text-xs font-mono uppercase tracking-widest text-[#6b7280]">
                03 — PHYSICAL BENCHMARKS
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#111418]">
                Verified performance metrics
              </h2>
            </div>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#111418] hover:bg-black text-white text-xs font-semibold tracking-wide transition self-start sm:self-auto"
            >
              <span>Launch 3D Studio</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-[#f9fafb] border border-neutral-200 rounded-2xl p-8 space-y-3 shadow-sm hover:shadow-md transition">
              <div className="text-5xl font-bold tracking-tight text-[#111418]">130</div>
              <div className="text-xs font-mono uppercase tracking-wider text-[#6b7280]">
                Meta Muse Calls
              </div>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Full cryptographic request receipts logged with model weights meta/muse-spark-1.3 and zero hardcoded fallbacks.
              </p>
            </div>

            <div className="bg-[#f9fafb] border border-neutral-200 rounded-2xl p-8 space-y-3 shadow-sm hover:shadow-md transition">
              <div className="text-5xl font-bold tracking-tight text-[#111418]">-83.9%</div>
              <div className="text-xs font-mono uppercase tracking-wider text-[#6b7280]">
                Prediction RMSE Drop
              </div>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Autonomous inductive revision from 8.29mm down to 0.047mm on held-out geometric drift predictions.
              </p>
            </div>

            <div className="bg-[#f9fafb] border border-neutral-200 rounded-2xl p-8 space-y-3 shadow-sm hover:shadow-md transition">
              <div className="text-5xl font-bold tracking-tight text-[#111418]">1,280</div>
              <div className="text-xs font-mono uppercase tracking-wider text-[#6b7280]">
                Q4 Continuum Elements
              </div>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Total Lagrangian 2D continuum mesh confirming 0.23% convergence consistency against beam solvers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 5: PROVENANCE & REPRODUCIBILITY
      ───────────────────────────────────────────────────────────── */}
      <section
        id="provenance"
        className="relative w-full min-h-screen flex flex-col justify-center px-8 sm:px-12 lg:px-16 py-20 bg-[#f8fafc] border-t border-neutral-200"
      >
        <div className="max-w-6xl mx-auto w-full space-y-16">
          <div className="max-w-xl space-y-3">
            <div className="text-xs font-mono uppercase tracking-widest text-[#6b7280]">
              04 — SCIENTIFIC PROVENANCE
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#111418]">
              Cryptographic audit logs & frozen artifacts
            </h2>
            <p className="text-sm text-[#4b5563] leading-relaxed">
              Every inference step, FEA residual norm, and hypothesis falsification check is recorded with immutable SHA-256 hashes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white border border-neutral-200/80 rounded-2xl p-8 space-y-4 shadow-sm hover:shadow-md transition">
              <div className="text-xs font-mono text-neutral-400">HASH 0x9f1b4a...</div>
              <h3 className="text-lg font-semibold text-[#111418]">Zero Fabrication</h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                All 130 Muse requests logged with response headers, seeds, and token distributions. No synthetic placeholders.
              </p>
            </div>
            <div className="bg-white border border-neutral-200/80 rounded-2xl p-8 space-y-4 shadow-sm hover:shadow-md transition">
              <div className="text-xs font-mono text-neutral-400">HASH 0x7e44c2...</div>
              <h3 className="text-lg font-semibold text-[#111418]">Corotational Convergence</h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                Full Newton-Raphson tangent residual histories verified to &lt; 1e-7 equilibrium tolerance across all load increments.
              </p>
            </div>
            <div className="bg-white border border-neutral-200/80 rounded-2xl p-8 space-y-4 shadow-sm hover:shadow-md transition">
              <div className="text-xs font-mono text-neutral-400">HASH 0x3d82a1...</div>
              <h3 className="text-lg font-semibold text-[#111418]">Independent Verification</h3>
              <p className="text-xs text-[#4b5563] leading-relaxed">
                One-command reproduction harness executing independent verification passes with code 0 exit status.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 5: FOOTER (100dvh FULL-VIEWPORT EDITORIAL MONUMENTAL STYLE)
      ───────────────────────────────────────────────────────────── */}
      <footer className="w-full h-[100dvh] max-h-[100dvh] bg-[#080a0f] text-[#94a3b8] pt-16 pb-8 px-8 sm:px-12 lg:px-16 border-t border-neutral-800/80 overflow-hidden relative flex flex-col justify-between selection:bg-white selection:text-black box-border">
        {/* Atmospheric top gradient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[850px] h-[340px] bg-gradient-to-b from-[#1e293b]/30 to-transparent blur-3xl pointer-events-none" />

        <div className="max-w-6xl mx-auto w-full relative z-10 flex-1 flex flex-col justify-between pt-2">
          {/* Top Multi-column Sitemap: Larger text & tighter balanced spacing */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12 text-sm">
            {/* Col 1 */}
            <div className="space-y-4">
              <h4 className="text-white font-semibold text-xs tracking-widest uppercase font-mono">Platform</h4>
              <ul className="space-y-3 text-neutral-400">
                <li>
                  <a
                    href="#candidates"
                    onClick={(e) => scrollToSection(e, "#candidates")}
                    className="hover:text-white transition cursor-pointer text-[13px]"
                  >
                    Verified Candidates
                  </a>
                </li>
                <li>
                  <a
                    href="#architecture"
                    onClick={(e) => scrollToSection(e, "#architecture")}
                    className="hover:text-white transition cursor-pointer text-[13px]"
                  >
                    Non-Linear FEA Solver
                  </a>
                </li>
                <li>
                  <a
                    href="#benchmarks"
                    onClick={(e) => scrollToSection(e, "#benchmarks")}
                    className="hover:text-white transition cursor-pointer text-[13px]"
                  >
                    Physical Benchmarks
                  </a>
                </li>
                <li>
                  <a
                    href="#provenance"
                    onClick={(e) => scrollToSection(e, "#provenance")}
                    className="hover:text-white transition cursor-pointer text-[13px]"
                  >
                    Scientific Provenance
                  </a>
                </li>
              </ul>
            </div>

            {/* Col 2 */}
            <div className="space-y-4">
              <h4 className="text-white font-semibold text-xs tracking-widest uppercase font-mono">Autonomous Science</h4>
              <ul className="space-y-3 text-neutral-400">
                <li>
                  <a
                    href="#architecture"
                    onClick={(e) => scrollToSection(e, "#architecture")}
                    className="text-neutral-300 hover:text-white transition cursor-pointer text-[13px] block"
                  >
                    Meta Muse Reasoning
                  </a>
                </li>
                <li>
                  <a
                    href="#candidates"
                    onClick={(e) => scrollToSection(e, "#candidates")}
                    className="text-neutral-300 hover:text-white transition cursor-pointer text-[13px] block"
                  >
                    Closed-Loop Discovery
                  </a>
                </li>
                <li>
                  <a
                    href="#benchmarks"
                    onClick={(e) => scrollToSection(e, "#benchmarks")}
                    className="text-neutral-300 hover:text-white transition cursor-pointer text-[13px] block"
                  >
                    Eigenvalue Stability Gates
                  </a>
                </li>
                <li>
                  <a
                    href="#provenance"
                    onClick={(e) => scrollToSection(e, "#provenance")}
                    className="text-neutral-300 hover:text-white transition cursor-pointer text-[13px] block"
                  >
                    Q4 Continuum Meshing
                  </a>
                </li>
              </ul>
            </div>

            {/* Col 3 */}
            <div className="space-y-4">
              <h4 className="text-white font-semibold text-xs tracking-widest uppercase font-mono">Verification Tools</h4>
              <ul className="space-y-3 text-neutral-400">
                <li>
                  <Link href="/dashboard#cad" className="text-neutral-300 hover:text-white transition text-[13px] block">
                    Interactive 3D CAD Studio
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard#arena" className="text-neutral-300 hover:text-white transition text-[13px] block">
                    Scientific Arena
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard#intent" className="text-neutral-300 hover:text-white transition text-[13px] block">
                    Hypothesis Intent Lab
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard#physics" className="text-neutral-300 hover:text-white transition text-[13px] block">
                    Multi-Fidelity Physics Solver
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 4 */}
            <div className="space-y-4">
              <h4 className="text-white font-semibold text-xs tracking-widest uppercase font-mono">Workspace</h4>
              <p className="text-neutral-400 text-[13px] leading-relaxed">
                Autonomous physics-guided generative mechanical engineering compiler for precision flexure systems.
              </p>
              <div className="pt-1">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white hover:bg-neutral-200 text-black text-xs font-semibold tracking-wide transition shadow-sm"
                >
                  <span>Open Studio</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>

          {/* Legal and Copyright bar: Pushed nicely above wordmark */}
          <div className="pt-8 pb-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-neutral-400 border-t border-neutral-800/70">
            <div className="flex items-center space-x-3">
              <span className="font-semibold text-white text-sm">Neodustria</span>
              <span>•</span>
              <span>Autonomous Generative Engineering Scientist © 2026</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/dashboard" className="text-neutral-300 hover:text-white transition font-medium">
                3D CAD Dashboard
              </Link>
              <span>•</span>
              <span className="text-neutral-500">All Rights Reserved</span>
            </div>
          </div>
        </div>

        {/* Monumental Wordmark: Lifted with bottom padding so it breathes cleanly */}
        <div className="w-full relative z-10 select-none overflow-hidden text-center flex items-center justify-center pointer-events-none pt-2 pb-4">
          <span className="text-[12.6vw] font-black tracking-[-0.04em] leading-none text-transparent bg-clip-text bg-gradient-to-b from-white/95 via-white/50 to-white/10 block w-full whitespace-nowrap uppercase">
            NEODUSTRIA
          </span>
        </div>
      </footer>
    </div>
  );
}

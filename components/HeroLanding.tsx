"use client";

import React from "react";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Activity,
  Box,
  Compass,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Flame,
  Zap,
} from "lucide-react";

interface HeroLandingProps {
  onEnterStudio: () => void;
  onEnterArena: () => void;
  onEnterIntent: () => void;
}

export default function HeroLanding({
  onEnterStudio,
  onEnterArena,
  onEnterIntent,
}: HeroLandingProps) {
  return (
    <div className="relative min-h-[calc(100vh-64px)] overflow-hidden bg-black text-white selection:bg-cyan-500 selection:text-black">
      {/* Precision CAD Engineering Grid Background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(14,165,233,0.15),rgba(255,255,255,0))] pointer-events-none" />
      <div 
        className="absolute inset-0 opacity-[0.14] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      {/* Floating Blueprint Coordinate Markers */}
      <div className="absolute top-10 left-12 text-[10px] font-mono text-neutral-600 select-none hidden lg:block">
        [SYS_COORD: 45.000, 27.500, 0.000] • TOL: ±0.005mm • ENVELOPE: 90×55×10mm
      </div>
      <div className="absolute top-10 right-12 text-[10px] font-mono text-cyan-500/60 select-none hidden lg:block">
        MUSE ENGINE: ACTIVE • RUNTIME: PHASE 23.5 FREEZE
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-16 pb-20 relative z-10 flex flex-col items-center">
        {/* Top Badges */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-neutral-900/90 border border-neutral-700/60 text-xs font-mono text-neutral-300 shadow-xl backdrop-blur-xl mb-8 hover:border-cyan-500/50 transition">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
          </span>
          <span className="text-cyan-400 font-semibold tracking-wide">META GLOBAL AI HACKATHON</span>
          <span className="text-neutral-500">•</span>
          <span className="text-neutral-300">Closed-Loop Generative Discovery</span>
        </div>

        {/* Hero Headline */}
        <div className="text-center max-w-4xl space-y-4">
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.08]">
            Autonomous Generative <br />
            <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
              Engineering Scientist
            </span>
          </h1>
          <p className="text-base sm:text-lg text-neutral-300 max-w-2xl mx-auto leading-relaxed font-normal">
            Bridging Meta Muse large reasoning models with deterministic non-linear corotational FEA, Q4 continuum continuum physics, and autonomous hypothesis revision.
          </p>
        </div>

        {/* Interactive CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 mt-9">
          <button
            onClick={onEnterStudio}
            className="group relative inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-bold text-sm tracking-wide shadow-lg shadow-cyan-500/25 hover:shadow-cyan-400/40 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
          >
            <Box className="w-4 h-4 text-black group-hover:rotate-12 transition-transform" />
            Launch 3D CAD Studio
            <ArrowRight className="w-4 h-4 text-black group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={onEnterArena}
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-neutral-900 hover:bg-neutral-800 text-white font-medium text-sm border border-neutral-700/80 hover:border-neutral-500 transition shadow-lg backdrop-blur-md cursor-pointer"
          >
            <Cpu className="w-4 h-4 text-indigo-400" />
            Explore Scientific Arena
          </button>

          <button
            onClick={onEnterIntent}
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-neutral-950/80 hover:bg-neutral-900 text-neutral-300 hover:text-white font-medium text-sm border border-neutral-800 hover:border-cyan-500/40 transition cursor-pointer"
          >
            <Zap className="w-4 h-4 text-amber-400" />
            Intent Lab Compiler
          </button>
        </div>

        {/* Real Engineering Telemetry Bar */}
        <div className="w-full max-w-5xl mt-16 grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
          <div className="bg-neutral-950/90 border border-neutral-800/80 rounded-xl p-4 shadow-xl flex flex-col justify-between hover:border-cyan-500/40 transition group">
            <div className="text-[11px] text-neutral-400 flex items-center justify-between">
              <span>MUSE API CALLS</span>
              <Activity className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition" />
            </div>
            <div className="text-2xl font-bold text-cyan-400 mt-2">130</div>
            <div className="text-[10px] text-neutral-500 mt-1">Authenticated receipts logged</div>
          </div>

          <div className="bg-neutral-950/90 border border-neutral-800/80 rounded-xl p-4 shadow-xl flex flex-col justify-between hover:border-emerald-500/40 transition group">
            <div className="text-[11px] text-neutral-400 flex items-center justify-between">
              <span>FALSIFICATION ERROR</span>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 group-hover:scale-110 transition" />
            </div>
            <div className="text-2xl font-bold text-emerald-400 mt-2">-83.9%</div>
            <div className="text-[10px] text-neutral-500 mt-1">Autonomous RMSE revision</div>
          </div>

          <div className="bg-neutral-950/90 border border-neutral-800/80 rounded-xl p-4 shadow-xl flex flex-col justify-between hover:border-blue-500/40 transition group">
            <div className="text-[11px] text-neutral-400 flex items-center justify-between">
              <span>CONTINUUM MESH</span>
              <Layers className="w-3.5 h-3.5 text-blue-400 group-hover:scale-110 transition" />
            </div>
            <div className="text-2xl font-bold text-blue-400 mt-2">1,280 Q4</div>
            <div className="text-[10px] text-neutral-500 mt-1">Total Lagrangian elements</div>
          </div>

          <div className="bg-neutral-950/90 border border-neutral-800/80 rounded-xl p-4 shadow-xl flex flex-col justify-between hover:border-amber-500/40 transition group">
            <div className="text-[11px] text-neutral-400 flex items-center justify-between">
              <span>CONVERGENCE ERROR</span>
              <Compass className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition" />
            </div>
            <div className="text-2xl font-bold text-amber-400 mt-2">0.23%</div>
            <div className="text-[10px] text-neutral-500 mt-1">Mesh-independent solver</div>
          </div>
        </div>

        {/* Interactive Feature Showcase Section */}
        <div className="w-full max-w-5xl mt-16 space-y-6">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
            <h2 className="text-xs font-mono uppercase tracking-widest text-neutral-400 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Core Autonomous Engineering Pillars
            </h2>
            <span className="text-[11px] font-mono text-neutral-500">ISO/ASTM COMPLIANT COMPLIANT MECHANISMS</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Card 1 */}
            <div 
              onClick={onEnterStudio}
              className="bg-neutral-950/70 border border-neutral-800/90 rounded-2xl p-6 hover:border-cyan-500/50 hover:bg-neutral-900/60 transition group cursor-pointer flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition">
                  <Box className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-cyan-400 transition">
                  Professional 3D CAD Orbit Viewport
                </h3>
                <p className="text-xs text-neutral-400 leading-relaxed">
                  Interactive real-time 3D solid geometry visualization with multi-axial camera orbit, Von Mises stress colormaps, animated deformation amplification, and strict physical envelope enforcement.
                </p>
              </div>
              <div className="mt-5 pt-3 border-t border-neutral-900 flex items-center justify-between text-xs font-mono text-cyan-400">
                <span>View CAD Models</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Card 2 */}
            <div 
              onClick={onEnterArena}
              className="bg-neutral-950/70 border border-neutral-800/90 rounded-2xl p-6 hover:border-indigo-500/50 hover:bg-neutral-900/60 transition group cursor-pointer flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-indigo-400 transition">
                  Autonomous Scientific Arena
                </h3>
                <p className="text-xs text-neutral-400 leading-relaxed">
                  Meta Muse inductive discovery engine: dimensionless scaling laws, automated falsification against nonlinear FEA, and continuous causal hypothesis refinement with verified audit ledgers.
                </p>
              </div>
              <div className="mt-5 pt-3 border-t border-neutral-900 flex items-center justify-between text-xs font-mono text-indigo-400">
                <span>Explore Arena</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Card 3 */}
            <div 
              onClick={onEnterIntent}
              className="bg-neutral-950/70 border border-neutral-800/90 rounded-2xl p-6 hover:border-amber-500/50 hover:bg-neutral-900/60 transition group cursor-pointer flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-amber-950/60 border border-amber-800/60 flex items-center justify-center text-amber-400 group-hover:scale-110 transition">
                  <Zap className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-amber-400 transition">
                  Natural Language Intent Lab
                </h3>
                <p className="text-xs text-neutral-400 leading-relaxed">
                  Translates high-level plain English engineering requirements directly into mathematically verifiable boundary value constraints, structural topology graphs, and automated repair loops.
                </p>
              </div>
              <div className="mt-5 pt-3 border-t border-neutral-900 flex items-center justify-between text-xs font-mono text-amber-400">
                <span>Try Intent Lab</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
        </div>

        {/* Footer info note */}
        <div className="mt-16 text-center text-xs font-mono text-neutral-500 border-t border-neutral-900 pt-6 w-full max-w-5xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Neodustria Phase 23.5 Reproduction Freeze Verified</span>
          </div>
          <div>
            Built with Next.js, Three.js & FastAPI • High-Precision Non-linear Corotational Beam Engine
          </div>
        </div>
      </div>
    </div>
  );
}

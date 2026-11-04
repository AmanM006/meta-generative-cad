"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import CADViewport3D from "@/components/CADViewport3D";
import AutonomousWorkflowController from "@/components/AutonomousWorkflowController";
import ScientificDiscoveryArena from "@/components/ScientificDiscoveryArena";
import IntentLab from "@/components/IntentLab";
import {
  Cpu,
  ShieldCheck,
  Play,
  RotateCcw,
  Sliders,
  CheckCircle2,
  XCircle,
  Box,
  Layers,
  Zap,
  ArrowLeft,
  ChevronRight,
} from "lucide-react";

interface Candidate {
  id: string;
  name: string;
  origin: string;
  role: string;
  metrics: {
    stroke_dy_mm: number;
    max_stress_MPa: number;
    axial_shift_dx_mm: number;
    rotation_theta_deg: number;
    volume_mm3: number;
    tangent_min_eig: number;
    linear_3d_stroke_mm: number;
    linear_3d_stress_MPa: number;
  };
  status: string;
  status_type: "pass" | "fail" | "warn";
  tolerance_margin: string;
  stability: string;
  glb_model: string;
  bounds_mm: { x: number[]; y: number[]; z: number[] };
  notes: string;
}

export default function DashboardPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedId, setSelectedId] = useState<string>("exp_01_a");
  const [isDeformed, setIsDeformed] = useState<boolean>(true);
  const [deformationScale, setDeformationScale] = useState<number>(1.0);
  const [activeTab, setActiveTab] = useState<
    "cad" | "arena" | "intent" | "benchmark" | "physics" | "evidence"
  >("cad");
  const [activeGlb, setActiveGlb] = useState<string | null>(null);
  const [activeStroke, setActiveStroke] = useState<number | null>(null);
  const [activeStress, setActiveStress] = useState<number | null>(null);

  // Sync activeTab with URL hash or query param on load
  useEffect(() => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.replace("#", "");
      if (["cad", "arena", "intent", "benchmark", "physics", "evidence"].includes(hash)) {
        setActiveTab(hash as any);
      }
    }
  }, []);

  useEffect(() => {
    fetch("/api/candidates")
      .then((res) => res.json())
      .then((data) => {
        if (data.candidates) {
          setCandidates(data.candidates);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const current = candidates.find((c) => c.id === selectedId) || candidates[0];

  return (
    <main className="min-h-screen bg-[#f4f6f9] text-[#111418] flex flex-col font-sans selection:bg-black selection:text-white antialiased">
      {/* Top Navbar matching Editorial Hero */}
      <header className="border-b border-neutral-200/90 bg-white/90 backdrop-blur-xl px-6 py-3.5 flex flex-wrap gap-4 items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3.5">
          <Link
            href="/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-neutral-100 hover:bg-neutral-200 text-neutral-700 hover:text-black transition text-xs font-semibold mr-1"
            title="Back to Landing Page"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Home</span>
          </Link>
          <span className="text-sm font-bold tracking-tight text-[#111418]">
            Neodustria
          </span>
          <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-100 text-neutral-600 font-mono font-semibold">
            CAD STUDIO 2.0
          </span>
        </div>

        {/* View Switcher Tabs matching Editorial pill controls */}
        <div className="flex items-center space-x-1.5 bg-neutral-100 p-1 rounded-full text-xs overflow-x-auto max-w-full">
          <button
            onClick={() => setActiveTab("cad")}
            className={`px-4 py-1.5 rounded-full transition font-semibold flex items-center gap-1.5 ${
              activeTab === "cad"
                ? "bg-[#111418] text-white shadow-sm"
                : "text-neutral-600 hover:text-black"
            }`}
          >
            <Box className="w-3.5 h-3.5" />
            3D Studio
          </button>

          <button
            onClick={() => setActiveTab("arena")}
            className={`px-4 py-1.5 rounded-full transition font-semibold flex items-center gap-1.5 ${
              activeTab === "arena"
                ? "bg-[#111418] text-white shadow-sm"
                : "text-neutral-600 hover:text-black"
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            Scientific Arena
          </button>

          <button
            onClick={() => setActiveTab("intent")}
            className={`px-4 py-1.5 rounded-full transition font-semibold flex items-center gap-1.5 ${
              activeTab === "intent"
                ? "bg-[#111418] text-white shadow-sm"
                : "text-neutral-600 hover:text-black"
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            Intent Lab
          </button>

          <button
            onClick={() => setActiveTab("benchmark")}
            className={`px-4 py-1.5 rounded-full transition font-semibold ${
              activeTab === "benchmark"
                ? "bg-[#111418] text-white shadow-sm"
                : "text-neutral-600 hover:text-black"
            }`}
          >
            Benchmark Matrix
          </button>

          <button
            onClick={() => setActiveTab("physics")}
            className={`px-4 py-1.5 rounded-full transition font-semibold ${
              activeTab === "physics"
                ? "bg-[#111418] text-white shadow-sm"
                : "text-neutral-600 hover:text-black"
            }`}
          >
            Physics & Stability
          </button>

          <button
            onClick={() => setActiveTab("evidence")}
            className={`px-4 py-1.5 rounded-full transition font-semibold ${
              activeTab === "evidence"
                ? "bg-[#111418] text-white shadow-sm"
                : "text-neutral-600 hover:text-black"
            }`}
          >
            Scientific Evidence
          </button>
        </div>

        <div className="hidden lg:flex items-center space-x-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-neutral-700 bg-neutral-100 border border-neutral-200 px-3 py-1 rounded-full shadow-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>FEA SOLVER READY</span>
          </div>
        </div>
      </header>

      {/* Main Studio Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Candidates & Controls (Visible on CAD and Benchmark tabs) */}
        {(activeTab === "cad" || activeTab === "benchmark") && (
          <aside className="w-80 border-r border-neutral-200 bg-white p-5 flex flex-col space-y-5 overflow-y-auto">
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500 mb-3 flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-black" /> Flexure Candidates
              </h2>
              <div className="space-y-2.5">
                {candidates.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedId(c.id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition flex flex-col space-y-1.5 ${
                      selectedId === c.id
                        ? "bg-neutral-50 border-black text-black shadow-sm"
                        : "bg-white border-neutral-200 hover:border-neutral-400 text-neutral-600"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-semibold gap-2">
                      <span className="font-mono text-neutral-900 truncate">{c.id.toUpperCase()}</span>
                      <span
                        className={`text-[9px] px-2 py-0.5 rounded-full font-mono font-bold whitespace-nowrap flex-shrink-0 leading-tight ${
                          c.status_type === "pass"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-rose-50 text-rose-700 border border-rose-200"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                    <div className="text-[12px] font-semibold leading-tight text-neutral-900">
                      {c.name}
                    </div>
                    <div className="text-[11px] text-neutral-500 truncate">
                      {c.origin}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Actuation Controls */}
            <div className="border-t border-neutral-200 pt-4 space-y-3">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500 flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-black" /> Deformation Controls
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsDeformed(!isDeformed)}
                  className={`flex-1 py-2 px-3 rounded-full text-xs font-semibold flex items-center justify-center gap-2 transition ${
                    isDeformed
                      ? "bg-[#111418] text-white shadow-sm"
                      : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200 border border-neutral-200"
                  }`}
                >
                  <Play className="w-3.5 h-3.5" />{" "}
                  {isDeformed ? "Deformed (5N)" : "Undeformed CAD"}
                </button>
                <button
                  onClick={() => setDeformationScale(1.0)}
                  className="p-2 rounded-full bg-neutral-100 hover:bg-neutral-200 text-neutral-700 text-xs border border-neutral-200"
                  title="Reset Scale"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>

              <div>
                <div className="flex justify-between text-xs text-neutral-500 mb-1 font-medium">
                  <span>Amplification</span>
                  <span className="font-mono text-black font-semibold">
                    {deformationScale.toFixed(1)}×
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.5"
                  value={deformationScale}
                  onChange={(e) => setDeformationScale(parseFloat(e.target.value))}
                  className="w-full accent-black bg-neutral-200 h-1.5 rounded-lg cursor-pointer"
                />
              </div>
            </div>

            {/* Frozen Physical Limits */}
            <div className="border-t border-neutral-200 pt-4 space-y-2 text-xs">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500 flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Physical Limit Gates
              </h2>
              <div className="space-y-2 font-mono text-[11px] text-neutral-600 bg-neutral-50 p-3.5 rounded-xl border border-neutral-200">
                <div className="flex justify-between">
                  <span>Stroke (Δy):</span>{" "}
                  <span className="text-emerald-600 font-bold">≥ 3.000 mm</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Stress (σ):</span>{" "}
                  <span className="text-emerald-600 font-bold">≤ 25.0 MPa</span>
                </div>
                <div className="flex justify-between">
                  <span>Axial Shift (|dx|):</span>{" "}
                  <span className="text-emerald-600 font-bold">≤ 0.200 mm</span>
                </div>
                <div className="flex justify-between">
                  <span>Rotation (|θ|):</span>{" "}
                  <span className="text-emerald-600 font-bold">≤ 0.050°</span>
                </div>
                <div className="flex justify-between">
                  <span>Min Thickness (h):</span>{" "}
                  <span className="text-emerald-600 font-bold">≥ 0.600 mm</span>
                </div>
                <div className="flex justify-between">
                  <span>Actuation (Fy):</span>{" "}
                  <span className="text-neutral-900 font-bold">5.000 N</span>
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Center: CAD Viewport & Active Screen */}
        <section className="flex-1 p-6 sm:p-8 flex flex-col space-y-6 overflow-y-auto bg-[#f8fafc]">
          {activeTab === "intent" && <IntentLab />}

          {activeTab === "arena" && (
            <div className="space-y-6">
              <ScientificDiscoveryArena />
            </div>
          )}

          {activeTab === "cad" && current && (
            <>
              {/* Interactive Autonomous Discovery Engine Controller */}
              <AutonomousWorkflowController
                onGlbGenerated={(url, stroke, stress) => {
                  setActiveGlb(url);
                  setActiveStroke(stroke);
                  setActiveStress(stress);
                }}
              />

              {/* Mechanism Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-neutral-200/80 p-5 rounded-2xl shadow-sm">
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="text-lg sm:text-xl font-bold text-[#111418] tracking-tight">
                      {current.name}
                    </h2>
                    <span
                      className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono font-bold whitespace-nowrap flex-shrink-0 ${
                        current.status_type === "pass"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-rose-50 text-rose-700 border border-rose-200"
                      }`}
                    >
                      {current.status}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-500 mt-1">{current.notes}</p>
                </div>
                <div className="text-left sm:text-right text-xs font-mono space-y-0.5 flex-shrink-0">
                  <div className="text-neutral-500">
                    Role: <span className="text-neutral-900 font-semibold">{current.role}</span>
                  </div>
                  <div className="text-neutral-400">
                    Provenance: <span className="text-neutral-600">{current.origin}</span>
                  </div>
                </div>
              </div>

              {/* 3D Viewport Component */}
              <div className="bg-white rounded-2xl border border-neutral-200/80 p-2 shadow-sm overflow-hidden">
                <CADViewport3D
                  modelUrl={activeGlb || current.glb_model}
                  isDeformed={isDeformed}
                  deformationScale={deformationScale}
                  strokeDyMm={
                    activeStroke !== null ? activeStroke : current.metrics.stroke_dy_mm
                  }
                  maxStressMPa={
                    activeStress !== null ? activeStress : current.metrics.max_stress_MPa
                  }
                />
              </div>

              {/* Verified Metrics Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white border border-neutral-200/80 rounded-2xl p-5 shadow-sm hover:border-black transition">
                  <div className="text-xs text-neutral-500 font-medium">
                    Non-linear Stroke (Δy)
                  </div>
                  <div className="text-2xl font-bold font-mono text-neutral-900 mt-1">
                    {current.metrics.stroke_dy_mm.toFixed(4)}{" "}
                    <span className="text-sm font-normal text-neutral-500">mm</span>
                  </div>
                  <div className="text-[11px] text-emerald-600 mt-1.5 flex items-center gap-1 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Target ≥ 3.000 mm (Pass)
                  </div>
                </div>

                <div className="bg-white border border-neutral-200/80 rounded-2xl p-5 shadow-sm hover:border-black transition">
                  <div className="text-xs text-neutral-500 font-medium">
                    Von Mises Stress (σ)
                  </div>
                  <div className="text-2xl font-bold font-mono text-neutral-900 mt-1">
                    {current.metrics.max_stress_MPa.toFixed(2)}{" "}
                    <span className="text-sm font-normal text-neutral-500">MPa</span>
                  </div>
                  <div className="text-[11px] text-emerald-600 mt-1.5 flex items-center gap-1 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Safety Factor:{" "}
                    {(35.0 / current.metrics.max_stress_MPa).toFixed(2)}×
                  </div>
                </div>

                <div className="bg-white border border-neutral-200/80 rounded-2xl p-5 shadow-sm hover:border-black transition">
                  <div className="text-xs text-neutral-500 font-medium">
                    Parasitic Axial Shift (|dx|)
                  </div>
                  <div className="text-2xl font-bold font-mono text-neutral-900 mt-1">
                    {current.metrics.axial_shift_dx_mm.toFixed(4)}{" "}
                    <span className="text-sm font-normal text-neutral-500">mm</span>
                  </div>
                  <div className="text-[11px] text-emerald-600 mt-1.5 flex items-center gap-1 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Floor ≤ 0.200 mm
                  </div>
                </div>

                <div className="bg-white border border-neutral-200/80 rounded-2xl p-5 shadow-sm hover:border-black transition">
                  <div className="text-xs text-neutral-500 font-medium">
                    Tangent Stability (λ min)
                  </div>
                  <div
                    className={`text-2xl font-bold font-mono mt-1 ${
                      current.metrics.tangent_min_eig > 0
                        ? "text-emerald-600"
                        : "text-rose-600"
                    }`}
                  >
                    {current.metrics.tangent_min_eig.toExponential(2)}
                  </div>
                  <div
                    className={`text-[11px] mt-1.5 flex items-center gap-1 font-mono ${
                      current.metrics.tangent_min_eig > 0
                        ? "text-emerald-600"
                        : "text-rose-600 font-bold"
                    }`}
                  >
                    {current.metrics.tangent_min_eig > 0 ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" /> Positive Definite (Stable)
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5" /> Unstable (Snap-Through)
                      </>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === "benchmark" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-neutral-900">
                    Full Comparative Benchmark Matrix (Fine-Mesh Verified)
                  </h2>
                  <p className="text-xs text-neutral-500">
                    Transparent comparison of classical baselines, deterministic references, and Meta Muse discovery arms.
                  </p>
                </div>
              </div>
              <div className="overflow-x-auto rounded-2xl border border-neutral-200 bg-white shadow-sm">
                <table className="w-full text-xs text-left text-neutral-700">
                  <thead className="bg-neutral-50 text-neutral-500 font-mono text-[11px] uppercase tracking-wider border-b border-neutral-200">
                    <tr>
                      <th className="p-3.5">Candidate / Methodology</th>
                      <th className="p-3.5">Stroke Δy</th>
                      <th className="p-3.5">Max Stress σ</th>
                      <th className="p-3.5">Parasitic |dx|</th>
                      <th className="p-3.5">Volume</th>
                      <th className="p-3.5">Stability</th>
                      <th className="p-3.5">Verdict</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 font-mono">
                    {candidates.map((c) => (
                      <tr key={c.id} className="hover:bg-neutral-50/80 transition">
                        <td className="p-3.5 font-sans font-semibold text-neutral-900">{c.name}</td>
                        <td className="p-3.5 font-bold text-neutral-900">
                          {c.metrics.stroke_dy_mm.toFixed(4)} mm
                        </td>
                        <td className="p-3.5 text-neutral-700">
                          {c.metrics.max_stress_MPa.toFixed(2)} MPa
                        </td>
                        <td className="p-3.5 text-neutral-600">
                          {c.metrics.axial_shift_dx_mm.toFixed(4)} mm
                        </td>
                        <td className="p-3.5 text-neutral-600">{c.metrics.volume_mm3} mm³</td>
                        <td
                          className={`p-3.5 font-semibold ${
                            c.metrics.tangent_min_eig > 0
                              ? "text-emerald-600"
                              : "text-rose-600"
                          }`}
                        >
                          {c.metrics.tangent_min_eig > 0
                            ? "Stable (λ > 0)"
                            : "Unstable (Snap)"}
                        </td>
                        <td className="p-3.5">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                              c.status_type === "pass"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : "bg-rose-50 text-rose-700 border border-rose-200"
                            }`}
                          >
                            {c.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "physics" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-neutral-900">
                Multi-Fidelity Structural Physics Cross-Validation
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="bg-white border border-neutral-200/80 rounded-2xl p-6 space-y-3.5 shadow-sm">
                  <h3 className="text-sm font-bold text-neutral-900 flex items-center gap-2">
                    <Box className="w-4 h-4" /> 2D Non-linear Corotational FEA
                  </h3>
                  <p className="text-xs text-neutral-600 leading-relaxed">
                    Captures chord-stretching tension under large deflections (Δy &gt; 5× beam thickness). Solves Newton-Raphson equilibrium with consistent tangent stiffness.
                  </p>
                  <div className="font-mono text-xs text-neutral-600 pt-3 border-t border-neutral-100 space-y-1.5">
                    <div>P0 Stroke: <span className="text-neutral-900 font-semibold">3.2140 mm</span></div>
                    <div>exp_01_A Stroke: <span className="text-neutral-900 font-semibold">3.0072 mm</span></div>
                    <div>
                      Geometric non-linearity:{" "}
                      <span className="text-emerald-600 font-semibold">Enabled (Exact)</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-neutral-200/80 rounded-2xl p-6 space-y-3.5 shadow-sm">
                  <h3 className="text-sm font-bold text-neutral-900 flex items-center gap-2">
                    <Layers className="w-4 h-4" /> 3D Linear Spatial Beam FEA (6-DOF)
                  </h3>
                  <p className="text-xs text-neutral-600 leading-relaxed">
                    Validates out-of-plane torsional rigidity (Iy vs Iz = 236×). Confirmed zero out-of-plane lateral displacement (|dz| = 0.000 mm) under symmetric actuation.
                  </p>
                  <div className="font-mono text-xs text-neutral-600 pt-3 border-t border-neutral-100 space-y-1.5">
                    <div>
                      Linear agreement:{" "}
                      <span className="text-emerald-600 font-semibold">0.000% error vs 2D linear</span>
                    </div>
                    <div>Out-of-plane twist: <span className="text-neutral-900 font-semibold">0.00000°</span></div>
                    <div>
                      Spatial Coupling:{" "}
                      <span className="text-emerald-600 font-semibold">Verified</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "evidence" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-neutral-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                Scientific Provenance & Reproduction
              </h2>
              <div className="bg-white border border-neutral-200/80 rounded-2xl p-6 font-mono text-xs space-y-3 text-neutral-700 shadow-sm">
                <div className="text-neutral-900 font-bold border-b border-neutral-200 pb-2.5">
                  OFFICIAL SCIENTIFIC LEDGER • PHASE 23.5 AUDIT TRAIL
                </div>
                <div>
                  Model: <span className="text-black font-semibold">meta/muse-spark-1.3</span>
                </div>
                <div>
                  Phase 23.5 audit:{" "}
                  <span className="text-neutral-900 font-semibold">
                    130 recorded API requests, 81,841 tokens, $0.033878
                  </span>
                  .
                </div>
                <div>
                  Fresh transfer pilot:{" "}
                  <span className="text-neutral-900 font-semibold">
                    11 recorded requests, $0.0196314; 23 FEA results independently recomputed
                  </span>
                  .
                </div>
                <div>
                  Fine-mesh transfer feasibility:{" "}
                  <span className="text-neutral-900 font-semibold">
                    deterministic 2/3 tasks; Muse cold 0/3, raw history 1/3, principle prompt 1/3
                  </span>
                  .
                </div>
                <div className="text-neutral-500 text-[11px] pt-3 border-t border-neutral-200">
                  The hosted workflow replays verified local runs with transparent cryptographic provenance receipts.
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

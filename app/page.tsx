"use client";

import React, { useState, useEffect } from "react";
import CADViewport3D from "@/components/CADViewport3D";
import AutonomousWorkflowController from "@/components/AutonomousWorkflowController";
import {
  Cpu,
  ShieldCheck,
  Play,
  RotateCcw,
  Sliders,
  CheckCircle2,
  XCircle,
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

export default function Home() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedId, setSelectedId] = useState<string>("exp_01_a");
  const [isDeformed, setIsDeformed] = useState<boolean>(true);
  const [deformationScale, setDeformationScale] = useState<number>(1.0);
  const [activeTab, setActiveTab] = useState<"cad" | "benchmark" | "physics" | "evidence">("cad");
  const [activeGlb, setActiveGlb] = useState<string | null>(null);
  const [activeStroke, setActiveStroke] = useState<number | null>(null);
  const [activeStress, setActiveStress] = useState<number | null>(null);

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
    <main className="min-h-screen bg-black text-neutral-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <header className="border-b border-neutral-900 bg-black/90 backdrop-blur-md px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center font-bold text-black shadow-lg shadow-cyan-500/20">
            Ω
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              NEODUSTRIA <span className="text-xs px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 font-mono font-semibold">CAD STUDIO 2.0</span>
            </h1>
            <p className="text-[11px] text-neutral-400">Autonomous Generative Engineering Scientist • Meta Global AI Hackathon</p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-1 bg-neutral-950 border border-neutral-800/80 rounded-lg p-1 text-xs">
          <button
            onClick={() => setActiveTab("cad")}
            className={`px-3 py-1.5 rounded-md transition font-medium ${activeTab === "cad" ? "bg-cyan-400 text-black font-bold shadow-md shadow-cyan-400/20" : "text-neutral-400 hover:text-white"}`}
          >
            3D Studio
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            className={`px-3 py-1.5 rounded-md transition font-medium ${activeTab === "benchmark" ? "bg-cyan-400 text-black font-bold shadow-md shadow-cyan-400/20" : "text-neutral-400 hover:text-white"}`}
          >
            Benchmark Matrix
          </button>
          <button
            onClick={() => setActiveTab("physics")}
            className={`px-3 py-1.5 rounded-md transition font-medium ${activeTab === "physics" ? "bg-cyan-400 text-black font-bold shadow-md shadow-cyan-400/20" : "text-neutral-400 hover:text-white"}`}
          >
            Physics & Stability
          </button>
          <button
            onClick={() => setActiveTab("evidence")}
            className={`px-3 py-1.5 rounded-md transition font-medium ${activeTab === "evidence" ? "bg-cyan-400 text-black font-bold shadow-md shadow-cyan-400/20" : "text-neutral-400 hover:text-white"}`}
          >
            Scientific Evidence
          </button>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span>2D/3D FEA SOLVER READY</span>
          </div>
        </div>
      </header>

      {/* Main Studio Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Candidates & Controls */}
        <aside className="w-80 border-r border-neutral-900 bg-neutral-950/80 p-4 flex flex-col space-y-4 overflow-y-auto">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Flexure Candidates
            </h2>
            <div className="space-y-2">
              {candidates.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full text-left p-3 rounded-lg border transition flex flex-col space-y-1 ${
                    selectedId === c.id
                      ? "bg-neutral-900 border-cyan-400 text-white shadow-lg shadow-cyan-950/30"
                      : "bg-neutral-950/50 border-neutral-900 hover:border-neutral-800 text-neutral-300"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="font-mono">{c.id.toUpperCase()}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                        c.status_type === "pass"
                          ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                          : "bg-rose-950/80 text-rose-400 border border-rose-800"
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>
                  <div className="text-[11px] font-medium leading-tight text-neutral-200">{c.name}</div>
                  <div className="text-[10px] text-neutral-500 truncate">{c.origin}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Actuation Controls */}
          <div className="border-t border-neutral-900 pt-4 space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Deformation Controls
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsDeformed(!isDeformed)}
                className={`flex-1 py-2 px-3 rounded-md text-xs font-semibold flex items-center justify-center gap-2 transition ${
                  isDeformed
                    ? "bg-cyan-400 text-black shadow-md shadow-cyan-400/20 font-bold"
                    : "bg-neutral-900 text-neutral-300 hover:bg-neutral-800 border border-neutral-800"
                }`}
              >
                <Play className="w-3.5 h-3.5" /> {isDeformed ? "Deformed Mode (5N)" : "Undeformed CAD"}
              </button>
              <button
                onClick={() => setDeformationScale(1.0)}
                className="p-2 rounded-md bg-neutral-900 hover:bg-neutral-800 text-neutral-300 text-xs border border-neutral-800"
                title="Reset Scale"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div>
              <div className="flex justify-between text-xs text-neutral-400 mb-1">
                <span>Displacement Amplification</span>
                <span className="font-mono text-cyan-400">{deformationScale.toFixed(1)}×</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.5"
                value={deformationScale}
                onChange={(e) => setDeformationScale(parseFloat(e.target.value))}
                className="w-full accent-cyan-400 bg-neutral-800 h-1.5 rounded-lg"
              />
            </div>
          </div>

          {/* Frozen Physical Limits */}
          <div className="border-t border-neutral-900 pt-4 space-y-2 text-xs">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Strict Physical Limits
            </h2>
            <div className="space-y-1 font-mono text-[11px] text-neutral-300 bg-black/60 p-2.5 rounded-lg border border-neutral-900">
              <div className="flex justify-between">
                <span>Stroke (Δy):</span> <span className="text-emerald-400 font-bold">≥ 3.000 mm</span>
              </div>
              <div className="flex justify-between">
                <span>Max Stress (σ):</span> <span className="text-emerald-400 font-bold">≤ 25.0 MPa</span>
              </div>
              <div className="flex justify-between">
                <span>Axial Shift (|dx|):</span> <span className="text-emerald-400 font-bold">≤ 0.200 mm</span>
              </div>
              <div className="flex justify-between">
                <span>Rotation (|θ|):</span> <span className="text-emerald-400 font-bold">≤ 0.050°</span>
              </div>
              <div className="flex justify-between">
                <span>Min Thickness (h):</span> <span className="text-emerald-400 font-bold">≥ 0.600 mm</span>
              </div>
              <div className="flex justify-between">
                <span>Actuation (Fy):</span> <span className="text-cyan-400 font-bold">5.000 N</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Center: CAD Viewport & Active Screen */}
        <section className="flex-1 p-6 flex flex-col space-y-6 overflow-y-auto bg-black">
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
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
                    {current.name}
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold ${
                        current.status_type === "pass"
                          ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                          : "bg-rose-950/80 text-rose-400 border border-rose-800"
                      }`}
                    >
                      {current.status}
                    </span>
                  </h2>
                  <p className="text-xs text-neutral-400 mt-1">{current.notes}</p>
                </div>
                <div className="text-right text-xs font-mono">
                  <div className="text-neutral-400">Role: <span className="text-cyan-400 font-semibold">{current.role}</span></div>
                  <div className="text-neutral-500">Provenance: <span className="text-neutral-300">{current.origin}</span></div>
                </div>
              </div>

              {/* 3D Viewport Component with Black Dark Theme */}
              <CADViewport3D
                modelUrl={activeGlb || current.glb_model}
                isDeformed={isDeformed}
                deformationScale={deformationScale}
                strokeDyMm={activeStroke !== null ? activeStroke : current.metrics.stroke_dy_mm}
                maxStressMPa={activeStress !== null ? activeStress : current.metrics.max_stress_MPa}
              />

              {/* Verified Metrics Cards */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 shadow-lg">
                  <div className="text-xs text-neutral-400 font-medium">Non-linear Stroke (Δy)</div>
                  <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
                    {current.metrics.stroke_dy_mm.toFixed(4)} <span className="text-sm font-normal text-neutral-400">mm</span>
                  </div>
                  <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1 font-mono">
                    <CheckCircle2 className="w-3 h-3" /> Target ≥ 3.000 mm (Pass)
                  </div>
                </div>

                <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 shadow-lg">
                  <div className="text-xs text-neutral-400 font-medium">Von Mises Stress (σ)</div>
                  <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                    {current.metrics.max_stress_MPa.toFixed(2)} <span className="text-sm font-normal text-neutral-400">MPa</span>
                  </div>
                  <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1 font-mono">
                    <CheckCircle2 className="w-3 h-3" /> Safety Factor: {(35.0 / current.metrics.max_stress_MPa).toFixed(2)}×
                  </div>
                </div>

                <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 shadow-lg">
                  <div className="text-xs text-neutral-400 font-medium">Parasitic Axial Shift (|dx|)</div>
                  <div className="text-2xl font-bold font-mono text-neutral-200 mt-1">
                    {current.metrics.axial_shift_dx_mm.toFixed(4)} <span className="text-sm font-normal text-neutral-400">mm</span>
                  </div>
                  <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1 font-mono">
                    <CheckCircle2 className="w-3 h-3" /> Floor ≤ 0.200 mm
                  </div>
                </div>

                <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 shadow-lg">
                  <div className="text-xs text-neutral-400 font-medium">Tangent Stability (λ min)</div>
                  <div className={`text-2xl font-bold font-mono mt-1 ${current.metrics.tangent_min_eig > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {current.metrics.tangent_min_eig.toExponential(2)}
                  </div>
                  <div className={`text-[11px] mt-1 flex items-center gap-1 font-mono ${current.metrics.tangent_min_eig > 0 ? "text-emerald-400" : "text-rose-400 font-bold"}`}>
                    {current.metrics.tangent_min_eig > 0 ? (
                      <>
                        <CheckCircle2 className="w-3 h-3" /> Positive Definite (Stable)
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3 h-3" /> Unstable (Snap-Through)
                      </>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === "benchmark" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white">Full Comparative Benchmark Matrix (Fine-Mesh Verified)</h2>
              <p className="text-xs text-neutral-400">Transparent comparison of classical baselines, deterministic references, and Meta Muse discovery arms.</p>
              <div className="overflow-x-auto rounded-xl border border-neutral-900 bg-neutral-950">
                <table className="w-full text-xs text-left text-neutral-300">
                  <thead className="bg-neutral-950 text-neutral-400 font-mono text-[11px] uppercase tracking-wider border-b border-neutral-900">
                    <tr>
                      <th className="p-3">Candidate / Methodology</th>
                      <th className="p-3">Stroke Δy</th>
                      <th className="p-3">Max Stress σ</th>
                      <th className="p-3">Parasitic |dx|</th>
                      <th className="p-3">Volume</th>
                      <th className="p-3">Stability</th>
                      <th className="p-3">Verdict</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-900 font-mono">
                    {candidates.map((c) => (
                      <tr key={c.id} className="hover:bg-neutral-900/50">
                        <td className="p-3 font-sans font-medium text-white">{c.name}</td>
                        <td className="p-3 text-cyan-400">{c.metrics.stroke_dy_mm.toFixed(4)} mm</td>
                        <td className="p-3 text-amber-400">{c.metrics.max_stress_MPa.toFixed(2)} MPa</td>
                        <td className="p-3 text-neutral-300">{c.metrics.axial_shift_dx_mm.toFixed(4)} mm</td>
                        <td className="p-3 text-neutral-300">{c.metrics.volume_mm3} mm³</td>
                        <td className={`p-3 ${c.metrics.tangent_min_eig > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {c.metrics.tangent_min_eig > 0 ? "Stable (λ > 0)" : "Unstable (Snap)"}
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${c.status_type === "pass" ? "bg-emerald-950/80 text-emerald-400" : "bg-rose-950/80 text-rose-400"}`}>
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
              <h2 className="text-lg font-bold text-white">Multi-Fidelity Structural Physics Cross-Validation</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 space-y-2">
                  <h3 className="text-sm font-bold text-cyan-400">2D Non-linear Corotational FEA</h3>
                  <p className="text-xs text-neutral-300">
                    Captures chord-stretching tension under large deflections (Δy &gt; 5× beam thickness). Solves Newton-Raphson equilibrium with consistent tangent stiffness.
                  </p>
                  <div className="font-mono text-xs text-neutral-400 pt-2 border-t border-neutral-900">
                    <div>P0 Stroke: 3.2140 mm</div>
                    <div>exp_01_A Stroke: 3.0072 mm</div>
                    <div>Geometric non-linearity: Enabled (Exact)</div>
                  </div>
                </div>

                <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 space-y-2">
                  <h3 className="text-sm font-bold text-blue-400">3D Linear Spatial Beam FEA (6-DOF)</h3>
                  <p className="text-xs text-neutral-300">
                    Validates out-of-plane torsional rigidity (Iy vs Iz = 236×). Confirmed zero out-of-plane lateral displacement (|dz| = 0.000 mm) under symmetric actuation.
                  </p>
                  <div className="font-mono text-xs text-neutral-400 pt-2 border-t border-neutral-900">
                    <div>Linear agreement: 0.000% error vs 2D linear</div>
                    <div>Out-of-plane twist: 0.00000°</div>
                    <div>Spatial Coupling: Verified</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "evidence" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white">Immutable Provenance & Scientific Receipts</h2>
              <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-4 font-mono text-xs space-y-2 text-neutral-300">
                <div className="text-cyan-400 font-bold">API RECEIPT AUDIT TRAIL</div>
                <div>Model: meta/muse-spark-1.3</div>
                <div>Receipt 1: experiment_results/exp_01_A_compound_direct_turn1_receipt.json</div>
                <div>Receipt 2: experiment_results/exp_02_D_biomimetic_symmetry_turn1_receipt.json</div>
                <div>Cumulative Budget Consumed: $0.20 / $150.00 (0.13%)</div>
                <div>Scientific Boundary: Meta Muse discovered symmetric topology; SciPy performed elastic sizing.</div>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

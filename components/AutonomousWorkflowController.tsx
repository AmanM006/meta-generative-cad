"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  Clock,
  Zap,
} from "lucide-react";

interface TimelineEvent {
  timestamp: string;
  run_id: string;
  step: string;
  title: string;
  status: string;
  details: Record<string, unknown>;
}

interface AutonomousRunState {
  run_id: string;
  status: "queued" | "in_progress" | "completed" | "failed" | "rejected" | "error";
  timeline: TimelineEvent[];
  result?: {
    verdict: string;
    stroke_dy_mm: number;
    peak_stress_MPa: number;
    parasitic_dx_mm: number;
    min_tangent_eigenvalue: number;
    glb_url: string;
    provenance: Record<string, unknown>;
  };
}

interface WorkflowControllerProps {
  onGlbGenerated: (glbUrl: string, stroke: number, stress: number) => void;
}

export default function AutonomousWorkflowController({ onGlbGenerated }: WorkflowControllerProps) {
  const [strokeTarget, setStrokeTarget] = useState<number>(3.0);
  const [appliedLoad, setAppliedLoad] = useState<number>(5.0);
  const [mode, setMode] = useState<string>("replay_hero");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runState, setRunState] = useState<AutonomousRunState | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const timelineEndRef = useRef<HTMLDivElement>(null);

  const startRun = async () => {
    setIsRunning(true);
    setRunState(null);
    setError(null);
    try {
      const res = await fetch("/backend/api/workflow/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stroke_target_mm: strokeTarget,
          load_fy_n: appliedLoad,
          max_stress_mpa: 25.0,
          mode: mode,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
      setActiveRunId(data.run_id);
    } catch (err) {
      console.error("Failed to trigger run:", err);
      setError(err instanceof Error ? err.message : "Backend unavailable");
      setIsRunning(false);
    }
  };

  useEffect(() => {
    if (!activeRunId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/backend/api/runs/${activeRunId}`);
        if (!res.ok) throw new Error(`Run lookup failed (${res.status})`);
        const data: AutonomousRunState = await res.json();
        setRunState(data);

        if (timelineEndRef.current) {
          timelineEndRef.current.scrollIntoView({ behavior: "smooth" });
        }

        if (data.status === "completed" || data.status === "failed" || data.status === "rejected" || data.status === "error") {
          setIsRunning(false);
          clearInterval(interval);
          if (data.result?.glb_url) {
            onGlbGenerated(data.result.glb_url, data.result.stroke_dy_mm, data.result.peak_stress_MPa);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
        setError(err instanceof Error ? err.message : "Run lookup failed");
        setIsRunning(false);
        clearInterval(interval);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [activeRunId, onGlbGenerated]);

  return (
    <div className="bg-neutral-950 border border-neutral-900 rounded-xl p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-900 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-cyan-950/60 border border-cyan-800/50 rounded-lg text-cyan-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-wide text-neutral-100 uppercase">
              Autonomous Discovery Studio
            </h2>
            <p className="text-xs text-neutral-400">
              Stored Muse Topology → Deterministic Compiler → Nonlinear FEA → SciPy Tuning
            </p>
          </div>
        </div>
        {activeRunId && (
          <div className="font-mono text-xs px-2.5 py-1 bg-black rounded border border-neutral-800 text-neutral-300">
            RUN ID: <span className="text-cyan-400">{activeRunId}</span>
          </div>
        )}
      </div>

      {/* Control Panel Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
        <div>
          <label className="text-neutral-400 block mb-1">Actuation Target</label>
          <div className="flex items-center bg-black border border-neutral-800 rounded px-3 py-2">
            <input
              type="number"
              step="0.1"
              value={strokeTarget}
              onChange={(e) => setStrokeTarget(parseFloat(e.target.value) || 3.0)}
              className="bg-transparent text-neutral-100 w-full focus:outline-none"
            />
            <span className="text-neutral-500 ml-1">mm</span>
          </div>
        </div>

        <div>
          <label className="text-neutral-400 block mb-1">Applied Actuation Load</label>
          <div className="flex items-center bg-black border border-neutral-800 rounded px-3 py-2">
            <input
              type="number"
              step="0.5"
              value={appliedLoad}
              onChange={(e) => setAppliedLoad(parseFloat(e.target.value) || 5.0)}
              className="bg-transparent text-neutral-100 w-full focus:outline-none"
            />
            <span className="text-neutral-500 ml-1">N</span>
          </div>
        </div>

        <div>
          <label className="text-neutral-400 block mb-1">Execution Mode</label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="w-full bg-black border border-neutral-800 rounded px-3 py-2 text-neutral-200 focus:outline-none"
          >
            <option value="replay_hero">Meta Muse exp_01_A (Stored Replay)</option>
            <option value="replay_p0">Deterministic P0 Double-Folded (Verified Replay)</option>
            <option value="replay_call3">Meta Muse Call 3 (Stored Replay)</option>
            <option value="dry_run">Dry Run Integration Test</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={startRun}
            disabled={isRunning}
            className={`w-full py-2 px-4 rounded font-medium flex items-center justify-center space-x-2 transition ${
              isRunning
                ? "bg-neutral-800 text-neutral-500 cursor-not-allowed"
                : "bg-cyan-600 hover:bg-cyan-500 text-black font-semibold shadow-lg shadow-cyan-950/50"
            }`}
          >
            {isRunning ? (
              <>
                <Clock className="w-4 h-4 animate-spin text-cyan-400" />
                <span>Executing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-black" />
                <span>Run Engineering Replay</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      <p className="text-xs text-neutral-500">Stored fixtures are recomputed locally. This control does not make a new Meta API call.</p>

      {/* Live Event Timeline HUD */}
      <div className="border border-neutral-900 bg-black rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between text-xs text-neutral-400 border-b border-neutral-900 pb-2">
          <span className="font-mono uppercase tracking-wider text-neutral-300">
            Real-Time Engineering Execution Stream
          </span>
          <span className="text-[10px]">
            {runState?.timeline ? `${runState.timeline.length} Milestones Logged` : "Idle / Waiting for Run"}
          </span>
        </div>

        <div className="max-h-64 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
          {!runState || runState.timeline.length === 0 ? (
            <div className="text-center py-6 text-neutral-600">
              Initiate a design cycle above to inspect real-time compiler, solver, and optimization events.
            </div>
          ) : (
            runState.timeline.map((ev, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded bg-neutral-950/80 border border-neutral-900/80 space-y-1 hover:border-neutral-800 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/40">
                      {ev.step}
                    </span>
                    <span className="font-semibold text-neutral-200">{ev.title}</span>
                  </div>
                  <span className="text-[10px] text-neutral-500">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-[11px] text-neutral-400 pl-2 border-l border-neutral-800">
                  {Object.entries(ev.details).map(([k, v]) => (
                    <div key={k} className="truncate">
                      <span className="text-neutral-500">{k}: </span>
                      <span className="text-neutral-300">
                        {typeof v === "object" ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
          <div ref={timelineEndRef} />
        </div>
      </div>
    </div>
  );
}

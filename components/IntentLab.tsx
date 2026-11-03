"use client";

import { useEffect, useState } from "react";

type Interpretation = {
  decision: string;
  constraints: Record<string, string | number | number[] | null>;
  missing?: string[];
  contradictions?: string[];
  unsupported?: string[];
};

type Graph = {
  anchors: number[][];
  stages: { center: number[]; height: number }[];
  connections: { from_type: string; from_index: number; from_port: string; to_type: string; to_index: number; to_port: string; thickness: number }[];
};

type IntentResult = {
  request_text: string;
  interpretation: Interpretation;
  scientific_plan: string[];
  execution_mode: string;
  safety_gate?: string;
  notice: string;
  provenance?: { model: string; request_id: string; cost_usd: number; response_sha256: string };
  physics?: {
    feasible: boolean;
    mesh_elements_per_beam: number;
    stroke_mm: number;
    absolute_drift_mm: number;
    stress_mpa: number;
    gates: Record<string, boolean>;
    constraint_margins: Record<string, number>;
    candidate_source: string;
    physical_scope: string;
    graph: Graph;
    envelope_mm: number[];
  } | null;
  repair?: {
    method: string;
    trials: { thickness_mm: number; stroke_mm: number; absolute_drift_mm: number; feasible: boolean }[];
    final: { feasible: boolean; mesh_elements_per_beam: number; stroke_mm: number; absolute_drift_mm: number; stress_mpa: number; graph: Graph };
    note: string;
  } | null;
  robustness?: {
    mesh_refinement: { elements_per_beam: number; stroke_mm: number; absolute_drift_mm: number; feasible: boolean }[];
    parameter_sensitivity: { case: string; stroke_mm: number; absolute_drift_mm: number; feasible: boolean }[];
    scope: string;
  } | null;
};

type Example = { id: string; request: string };

const LABELS: Record<string, string> = {
  material: "Material", force_n: "Actuation force", stroke_min_mm: "Minimum stroke",
  envelope_mm: "Package", drift_max_mm: "Maximum lateral drift", stress_max_mpa: "Maximum stress",
};
const UNITS: Record<string, string> = {
  force_n: "N", stroke_min_mm: "mm", envelope_mm: "mm", drift_max_mm: "mm", stress_max_mpa: "MPa",
};

function GraphSketch({graph, envelope}: {graph: Graph; envelope: number[]}) {
  const point = (kind: string, index: number, port: string) => {
    if (kind === "anchor") return graph.anchors[index];
    const stage = graph.stages[index];
    return [stage.center[0], stage.center[1] + (port === "top" ? stage.height/2 : port === "bot" ? -stage.height/2 : 0)];
  };
  const x = (v: number) => v*1000;
  const y = (v: number) => envelope[1]-v*1000;
  return <svg aria-label="Plan view of the evaluated structural graph" role="img" viewBox={`-3 -3 ${envelope[0]+6} ${envelope[1]+6}`} className="w-full h-44 rounded-lg border border-neutral-800 bg-black">
    {graph.connections.map((edge, i) => {
      const a = point(edge.from_type, edge.from_index, edge.from_port);
      const b = point(edge.to_type, edge.to_index, edge.to_port);
      return <line key={i} x1={x(a[0])} y1={y(a[1])} x2={x(b[0])} y2={y(b[1])} stroke="#22d3ee" strokeWidth={Math.max(.8, edge.thickness*1400)} />;
    })}
    {graph.stages.map((stage, i) => <line key={i} x1={x(stage.center[0])} y1={y(stage.center[1]-stage.height/2)} x2={x(stage.center[0])} y2={y(stage.center[1]+stage.height/2)} stroke="#a5b4fc" strokeWidth="2.5" />)}
    {graph.anchors.map((anchor, i) => <circle key={i} cx={x(anchor[0])} cy={y(anchor[1])} r="1.8" fill="#fbbf24" />)}
  </svg>;
}

export default function IntentLab() {
  const [request, setRequest] = useState("Design a PP guide for 4 N load, 2 mm stroke, 90 x 55 mm package with drift under 0.06 mm.");
  const [examples, setExamples] = useState<Example[]>([]);
  const [result, setResult] = useState<IntentResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/backend/api/intent/examples")
      .then(async (r) => { if (!r.ok) throw new Error("Example evidence unavailable"); return r.json(); })
      .then((d) => setExamples(d.examples || []))
      .catch(() => setExamples([]));
  }, []);

  async function run(payload: Record<string, string>) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch("/backend/api/intent/interpret", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Backend returned ${response.status}`);
      setResult(data);
      setRequest(data.request_text);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Interpretation failed");
    } finally {
      setBusy(false);
    }
  }

  const isRecorded = result?.execution_mode.startsWith("RECORDED_");
  const failedGates = Object.entries(result?.physics?.gates || {}).filter(([, pass]) => !pass).map(([name]) => name);

  return <div className="space-y-5 max-w-5xl mx-auto w-full">
    <div className="rounded-2xl border border-cyan-800/50 bg-gradient-to-br from-cyan-950/35 via-neutral-950 to-indigo-950/30 p-6">
      <div className="text-xs uppercase tracking-[0.2em] text-cyan-400 font-semibold">Engineering intent laboratory</div>
      <h2 className="text-2xl font-semibold mt-2">From a written problem to a testable physical specification</h2>
      <p className="text-sm text-neutral-400 mt-2 max-w-3xl">Enter a request to compile explicit constraints and find missing or conflicting requirements. Recorded Muse examples show model interpretation beside independent nonlinear FEA results. The hosted app does not make new Muse or solver calls.</p>
    </div>

    <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 space-y-4">
      <label htmlFor="engineering-request" className="block text-sm font-medium">Describe the engineering problem</label>
      <textarea id="engineering-request" value={request} onChange={(event) => setRequest(event.target.value)} rows={3}
        className="w-full rounded-lg border border-neutral-700 bg-black p-3 text-sm text-neutral-100 focus:outline-none focus:border-cyan-400" />
      <div className="flex flex-wrap items-center gap-2">
        <button disabled={busy} onClick={() => run({mode: "deterministic", request_text: request})}
          className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50">Interpret entered request</button>
        <span className="text-xs text-neutral-500">Live deterministic compilation · no physical verdict until FEA</span>
      </div>
      <div className="border-t border-neutral-800 pt-4">
        <p className="text-xs uppercase tracking-wide text-neutral-400 mb-2">Recorded Muse + physics examples</p>
        <div className="flex flex-wrap gap-2">
          {examples.map((example) => <button key={example.id} disabled={busy}
            onClick={() => run({mode: "recorded_muse", example_id: example.id})}
            className="rounded-lg border border-indigo-700/70 bg-indigo-950/40 px-3 py-2 text-xs hover:bg-indigo-900/60 disabled:opacity-50">
            {example.id === "C01" ? "Drift failure" : example.id === "C02" ? "Feasible screen" : example.id === "C09" ? "Contradictory request" : "Safety gate catches model"}
          </button>)}
        </div>
      </div>
      {busy && <p className="text-sm text-cyan-300">Reading evidence…</p>}
      {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
    </div>

    {result && <div className="space-y-4">
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
        <div className="flex flex-wrap justify-between gap-2 mb-4">
          <h3 className="font-semibold">Engineering interpretation</h3>
          <span className={`rounded-full px-3 py-1 text-xs font-mono ${isRecorded ? "bg-indigo-950 text-indigo-300" : "bg-cyan-950 text-cyan-300"}`}>{result.execution_mode}</span>
        </div>
        <p className="text-sm text-neutral-300 mb-4">{result.request_text}</p>
        <p className="text-sm mb-4">Decision: <strong className="text-cyan-300">{result.interpretation.decision.replaceAll("_", " ")}</strong></p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {Object.entries(result.interpretation.constraints).map(([key, value]) => <div key={key} className="rounded-lg border border-neutral-800 bg-black p-3">
            <div className="text-xs text-neutral-500">{LABELS[key] || key}</div>
            <div className="font-mono text-sm mt-1">{value === null ? <span className="text-amber-300">Missing</span> : `${Array.isArray(value) ? value.join(" × ") : value} ${UNITS[key] || ""}`}</div>
          </div>)}
        </div>
        {!!result.interpretation.missing?.length && <p className="text-xs text-amber-300 mt-3">Clarify: {result.interpretation.missing.join(", ")}</p>}
        {!!result.interpretation.contradictions?.length && <p className="text-xs text-rose-300 mt-3">Contradiction: {result.interpretation.contradictions.join("; ")}</p>}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
          <h3 className="font-semibold mb-3">Scientific plan</h3>
          <ol className="list-decimal pl-5 space-y-2 text-sm text-neutral-300">{result.scientific_plan.map((step, i) => <li key={i}>{step}</li>)}</ol>
          {result.safety_gate?.startsWith("blocked") && <p className="text-xs text-rose-300 mt-4">Independent safety gate blocked this model output.</p>}
        </div>
        <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
          <h3 className="font-semibold mb-3">Physics verification</h3>
          {result.physics ? <>
            <p className={`text-sm font-semibold ${result.physics.feasible ? "text-emerald-300" : "text-rose-300"}`}>{result.physics.feasible ? "Beam-model screen passed" : `Rejected: ${failedGates.join(", ") || "solver failure"}`}</p>
            <div className="mt-3"><GraphSketch graph={result.physics.graph} envelope={result.physics.envelope_mm} /></div>
            <div className="grid grid-cols-3 gap-2 mt-4 font-mono text-xs">
              <div>Stroke<br/><strong>{result.physics.stroke_mm.toFixed(3)} mm</strong></div>
              <div>Abs. drift<br/><strong>{result.physics.absolute_drift_mm.toFixed(3)} mm</strong></div>
              <div>Stress<br/><strong>{result.physics.stress_mpa.toFixed(2)} MPa</strong></div>
            </div>
            <div className="mt-4 text-xs text-neutral-400 space-y-1">
              {Object.entries(result.physics.constraint_margins).map(([key, margin]) => <p key={key}>{key.replaceAll("_", " ")} margin: <span className={margin >= 0 ? "text-emerald-300" : "text-rose-300"}>{margin.toFixed(3)}</span></p>)}
              <p>Mesh: {result.physics.mesh_elements_per_beam} elements per beam · candidate: deterministic two-stage template</p>
            </div>
          </> : <p className="text-sm text-neutral-400">No physical result for this interpretation. A valid specification and solver run are required.</p>}
        </div>
      </div>
      {result.repair && <div className="rounded-xl border border-emerald-800/60 bg-emerald-950/20 p-5">
        <div className="text-xs uppercase tracking-wide text-emerald-300">Measured correction · deterministic sizing</div>
        <h3 className="font-semibold mt-1">The failed drift constraint was repaired</h3>
        <p className="text-sm text-neutral-300 mt-2">The original graph missed the 0.030 mm drift limit. Four recorded thickness trials retained its connectivity and found a fine-mesh feasible design.</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
          {result.repair.trials.map((trial) => <div key={trial.thickness_mm} className="rounded-lg border border-neutral-700 bg-black/50 p-3 text-xs font-mono">
            <div className="text-neutral-400">{trial.thickness_mm.toFixed(1)} mm beam</div>
            <div className={trial.feasible ? "text-emerald-300 mt-1" : "text-rose-300 mt-1"}>{trial.feasible ? "Passed coarse mesh" : "Failed drift"}</div>
            <div className="mt-1">Drift {trial.absolute_drift_mm.toFixed(4)} mm</div>
          </div>)}
        </div>
        <p className="text-sm text-emerald-300 mt-4">Fine mesh ({result.repair.final.mesh_elements_per_beam}/beam): {result.repair.final.stroke_mm.toFixed(3)} mm stroke · {result.repair.final.absolute_drift_mm.toFixed(4)} mm drift · {result.repair.final.stress_mpa.toFixed(2)} MPa stress.</p>
        <p className="text-xs text-neutral-400 mt-2">{result.repair.note}</p>
      </div>}
      {result.robustness && <div className="rounded-xl border border-amber-800/60 bg-amber-950/20 p-5 text-sm">
        <h3 className="font-semibold text-amber-200">Robustness boundary</h3>
        <p className="text-neutral-300 mt-2">All four mesh densities and four individual ±5% thickness / ±10% stiffness checks passed. The combined thinner, softer case failed drift: 0.0323 mm against the 0.0300 mm limit.</p>
        <p className="text-xs text-neutral-400 mt-2">{result.robustness.scope}</p>
      </div>}
      <p className="text-xs text-neutral-500">{result.notice}{result.provenance && ` · Muse receipt ${result.provenance.request_id} · cost $${result.provenance.cost_usd.toFixed(6)}`}</p>
    </div>}

    <p className="text-xs text-neutral-500">Frozen 16-request confirmation: Muse cold 15/16 fully correct specifications, fixed rules parser 7/16, counterexample memory 14/16. A later Gemini 2.5 Flash control passed 9/10 completed cases before its API quota stopped the run; there is no full LLM comparison. One of four recorded design screens passed fine-mesh beam FEA. These are numerical screens, not fabrication certification.</p>
  </div>;
}

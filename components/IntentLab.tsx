"use client";

import { useEffect, useState } from "react";

type Interpretation = {
  decision: string;
  constraints: Record<string, string | number | number[] | null>;
  missing?: string[];
  contradictions?: string[];
  unsupported?: string[];
  ambiguities?: string[];
  uncertainties?: string[];
  material_properties?: { measured_E_gpa: number | null };
  model_issue_codes?: string[];
};

type Graph = {
  anchors: number[][];
  stages: { center: number[]; height: number }[];
  connections: { from_type: string; from_index: number; from_port: string; to_type: string; to_index: number; to_port: string; thickness: number }[];
};

type IntentResult = {
  request_text: string;
  interpretation: Interpretation;
  clarification?: { action: string; field?: string; question: string | null; reason: string; remaining_required?: string[]; ranking_provenance?: string };
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
  robust_search?: {
    candidate_thicknesses_mm: number[]; coarse_pass: boolean[]; selected_thickness_mm: number | null;
    fine_scenarios: { name: string; feasible: boolean; stroke_mm: number; absolute_drift_mm: number; stress_mpa: number }[];
    fine_robust: boolean; scope: string; clearance: string;
  } | null;
  loop?: {
    muse_question: string; muse_question_field: string; scripted_answer: string;
    solver_assumptions: string[];
    trials: { thickness_mm: number; coarse_feasible: boolean; coarse_failed_gates: string[]; fine_feasible: boolean | null }[];
    selected_thickness_mm: number | null; verdict: string;
  };
  initial_joint_failure?: { candidate_thickness_mm: number; scenario: string; absolute_drift_mm: number; drift_limit_mm: number };
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
  const [clarificationExamples, setClarificationExamples] = useState<Example[]>([]);
  const [loopExamples, setLoopExamples] = useState<Example[]>([]);
  const [localLiveExamples, setLocalLiveExamples] = useState<Example[]>([]);
  const [result, setResult] = useState<IntentResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");

  useEffect(() => {
    fetch("/backend/api/intent/examples")
      .then(async (r) => { if (!r.ok) throw new Error("Example evidence unavailable"); return r.json(); })
      .then((d) => { setExamples(d.examples || []); setClarificationExamples(d.clarification_examples || []); setLoopExamples(d.loop_examples || []); setLocalLiveExamples(d.local_live_examples || []); })
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
      {!!clarificationExamples.length && <div className="border-t border-neutral-800 pt-4">
        <p className="text-xs uppercase tracking-wide text-neutral-400 mb-2">Recorded Muse clarification questions</p>
        <div className="flex flex-wrap gap-2">{clarificationExamples.map((example) => <button key={example.id} disabled={busy}
          onClick={() => run({mode: "recorded_clarification", example_id: example.id})}
          className="rounded-lg border border-violet-700/70 bg-violet-950/40 px-3 py-2 text-xs hover:bg-violet-900/60 disabled:opacity-50">
          {example.id === "Q02" ? "Missing force" : example.id === "Q03" ? "Missing stroke" : example.id === "Q04" ? "Missing material" : example.id === "Q12" ? "Uncertain modulus" : "Material choice"}
        </button>)}</div>
      </div>}
      {!!loopExamples.length && <div className="border-t border-neutral-800 pt-4">
        <p className="text-xs uppercase tracking-wide text-neutral-400 mb-2">Recorded end-to-end solver loops · scripted answers</p>
        <div className="flex flex-wrap gap-2">{loopExamples.map((example) => <button key={example.id} disabled={busy}
          onClick={() => run({mode: "recorded_loop", example_id: example.id})}
          className="rounded-lg border border-emerald-700/70 bg-emerald-950/30 px-3 py-2 text-xs hover:bg-emerald-900/50 disabled:opacity-50">
          {example.id === "Q02" ? "Ask force → repair" : example.id === "Q03" ? "Ask stroke → verify" : "Ask material → repair"}
        </button>)}</div>
      </div>}
      {!!localLiveExamples.length && <div className="border-t border-neutral-800 pt-4">
        <p className="text-xs uppercase tracking-wide text-neutral-400 mb-2">Genuine local Muse call + solver · audited replay</p>
        <button disabled={busy} onClick={() => run({mode: "recorded_local_live", example_id: "L01"})}
          className="rounded-lg border border-cyan-700/70 bg-cyan-950/40 px-3 py-2 text-xs hover:bg-cyan-900/60 disabled:opacity-50">
          Live Muse question → failed tolerance → robust repair
        </button>
      </div>}
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
      {result.loop && <div className="rounded-xl border border-violet-800/60 bg-violet-950/20 p-5 text-sm">
        <div className="text-xs uppercase tracking-wide text-violet-300">Recorded engineering interaction · scripted user answer</div>
        <h3 className="font-semibold mt-1">Describe → Clarify → Formalize → Simulate → Repair → Verify</h3>
        <p className="mt-3 text-neutral-300"><strong>Muse asked:</strong> {result.loop.muse_question}</p>
        <p className="mt-2 text-neutral-300"><strong>Scripted answer:</strong> {result.loop.scripted_answer}</p>
        <p className="mt-2 text-neutral-300"><strong>Solver:</strong> Five predeclared thicknesses, coarse screening and fine verification of coarse passes. Selected {result.loop.selected_thickness_mm?.toFixed(1) ?? "none"} mm; {result.loop.verdict.replaceAll("_", " ")}.</p>
        <div className="flex flex-wrap gap-2 mt-3">{result.loop.trials.map((trial) => <div key={trial.thickness_mm} className="rounded-lg border border-neutral-700 bg-black/40 p-2 text-xs font-mono">
          {trial.thickness_mm.toFixed(1)} mm · {trial.fine_feasible === true ? "fine PASS" : trial.coarse_feasible ? "fine FAIL" : `coarse FAIL ${trial.coarse_failed_gates.join(", ")}`}
        </div>)}</div>
        <p className="text-xs text-neutral-400 mt-3">Solver assumptions: {result.loop.solver_assumptions.join("; ")}. These are recorded scripted fixtures, not live user conversations.</p>
      </div>}
      {result.initial_joint_failure && <div className="rounded-xl border border-rose-800/60 bg-rose-950/20 p-4 text-sm">
        <strong>First nominal design failed joint uncertainty.</strong> The {result.initial_joint_failure.candidate_thickness_mm.toFixed(1)} mm candidate drifted {result.initial_joint_failure.absolute_drift_mm.toFixed(4)} mm in the {result.initial_joint_failure.scenario.replaceAll("_", " ")} case, above the {result.initial_joint_failure.drift_limit_mm.toFixed(4)} mm limit. The solver then tested the next predeclared thickness.
      </div>}
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
        {!!result.interpretation.ambiguities?.length && <p className="text-xs text-amber-300 mt-3">Ambiguity: {result.interpretation.ambiguities.join("; ")}</p>}
        {!!result.interpretation.uncertainties?.length && <p className="text-xs text-amber-300 mt-3">Material uncertainty: {result.interpretation.uncertainties.join("; ")}</p>}
        {!!result.interpretation.model_issue_codes?.length && <p className="text-xs text-violet-300 mt-3">Recorded model issue codes: {result.interpretation.model_issue_codes.join(", ")}</p>}
        {result.interpretation.material_properties?.measured_E_gpa != null && <p className="text-xs text-cyan-300 mt-3">Measured batch modulus: {result.interpretation.material_properties.measured_E_gpa} GPa</p>}
        {result.clarification?.action === "clarify" && <div className="mt-4 rounded-lg border border-amber-700/50 bg-amber-950/20 p-4">
          <p className="text-sm text-amber-200">Next question: {result.clarification.question}</p>
          <div className="flex flex-wrap gap-2 mt-3">
            <input aria-label="Answer clarification question" value={answer} onChange={(event) => setAnswer(event.target.value)}
              className="min-w-44 flex-1 rounded-lg border border-neutral-700 bg-black p-2 text-sm" placeholder="Enter the missing value" />
            <button disabled={busy || !answer.trim()} onClick={() => {
              const prefix: Record<string, string> = {force_n: "force", stroke_min_mm: "stroke", material: "material", envelope_mm: "package", material_properties: "measured modulus"};
              const field = result.clarification?.field || "";
              const next = `${result.request_text} ${prefix[field] || field} ${answer.trim()}.`;
              setAnswer("");
              run({mode: "deterministic", request_text: next});
            }} className="rounded-lg bg-amber-300 px-3 py-2 text-sm font-semibold text-black disabled:opacity-50">Apply answer</button>
          </div>
          <p className="text-xs text-neutral-500 mt-2">Deterministic question priority; no Muse or FEA call. {result.clarification.remaining_required?.length} required field(s) remain.</p>
        </div>}
        {result.clarification?.action === "abstain" && <p className="text-xs text-rose-300 mt-3">Clarification halted: {result.clarification.reason}</p>}
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
      {result.robust_search && <div className="rounded-xl border border-emerald-800/60 bg-emerald-950/20 p-5 text-sm">
        <h3 className="font-semibold text-emerald-200">Joint uncertainty design screen</h3>
        <p className="text-neutral-300 mt-2">A deterministic {result.robust_search.candidate_thicknesses_mm.length}-candidate thickness search selected {result.robust_search.selected_thickness_mm?.toFixed(1)} mm. All four joint thickness and modulus cases passed the fine beam mesh.</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3">{result.robust_search.fine_scenarios.map((row) => <div key={row.name} className="rounded-lg border border-neutral-700 bg-black/40 p-2 text-xs font-mono">
          <div>{row.name.replaceAll("_", " ")}</div><div className={row.feasible ? "text-emerald-300" : "text-rose-300"}>{row.feasible ? "PASS" : "FAIL"}</div>
          <div>{row.stroke_mm.toFixed(3)} mm stroke</div><div>{row.absolute_drift_mm.toFixed(4)} mm drift</div>
        </div>)}</div>
        <p className="text-xs text-neutral-400 mt-3">{result.robust_search.scope}. Clearance: {result.robust_search.clearance}.</p>
      </div>}
      <p className="text-xs text-neutral-500">{result.notice}{result.provenance && ` · Muse receipt ${result.provenance.request_id} · cost $${result.provenance.cost_usd.toFixed(6)}`}</p>
    </div>}

    <p className="text-xs text-neutral-500">Frozen 16-request specification result: Muse cold 15/16, rules 7/16. New frozen 20-request clarification result: Muse cold 15/20, raw memory 16/20, validated memory 16/20, rules 6/20. The new study had one unsupported field assumption in each Muse arm and no matched Gemini control. Three solver loops reuse recorded Muse questions; one additional loop contains a genuine local Muse call. All user answers were scripted. These are numerical beam screens, not fabrication certification.</p>
  </div>;
}

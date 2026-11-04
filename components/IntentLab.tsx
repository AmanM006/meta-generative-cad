"use client";

import { useEffect, useState } from "react";
import LiveEngineeringAgent from "./LiveEngineeringAgent";

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
  reference_score?: { full_case?: boolean; complete_correct?: boolean };
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
    <div className="rounded-2xl border border-neutral-200/90 bg-white p-6 sm:p-7 shadow-sm">
      <div className="text-xs uppercase tracking-[0.2em] text-neutral-500 font-mono font-semibold">Engineering intent laboratory</div>
      <h2 className="text-2xl font-bold text-neutral-900 mt-2">From a written problem to a testable physical specification</h2>
      <p className="text-sm text-neutral-600 mt-2 max-w-3xl leading-relaxed">Enter a request to compile explicit constraints and find missing or conflicting requirements. The access-code panel runs fresh Muse and beam screening when configured. Examples below it are recorded replays.</p>
    </div>

    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm space-y-2">
        <div className="text-xs uppercase tracking-wider text-neutral-500 font-mono font-semibold">Fresh wording · 12 cases</div>
        <div className="text-3xl font-bold text-neutral-900 mt-1">10/12 <span className="text-sm font-normal text-neutral-500 font-sans">Muse</span></div>
        <div className="text-xs text-neutral-600 leading-relaxed">4/12 revised rules · 72/72 fields extracted by Muse</div>
      </div>
      <div className="rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm space-y-2">
        <div className="text-xs uppercase tracking-wider text-neutral-500 font-mono font-semibold">Original frozen rules · 20 cases</div>
        <div className="text-3xl font-bold text-neutral-900 mt-1">15/20 <span className="text-sm font-normal text-neutral-500 font-sans">Muse</span></div>
        <div className="text-xs text-neutral-600 leading-relaxed">6/20 original rules · revised rules scored 19/20 only after seeing those cases</div>
      </div>
      <div className="rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm space-y-2">
        <div className="text-xs uppercase tracking-wider text-neutral-500 font-mono font-semibold">Evidence boundary</div>
        <div className="text-xs text-neutral-600 mt-1 leading-relaxed">Project-authored tasks. Gemini control stopped at 1/20 on quota. Solver results are beam-model screens.</div>
        <a href="https://github.com/AmanM006/neodustria-ai/blob/master/SOURCE_AND_EVIDENCE.md" target="_blank" rel="noreferrer" className="inline-block mt-2 text-xs font-semibold text-neutral-900 underline underline-offset-2 hover:text-black">Inspect source and raw evidence →</a>
      </div>
    </div>

    <LiveEngineeringAgent />

    <div className="rounded-2xl border border-neutral-200/90 bg-white p-6 sm:p-7 space-y-5 shadow-sm">
      <label htmlFor="engineering-request" className="block text-sm font-semibold text-neutral-900">Describe the engineering problem</label>
      <textarea id="engineering-request" value={request} onChange={(event) => setRequest(event.target.value)} rows={3}
        className="w-full rounded-xl border border-neutral-300 bg-neutral-50 p-3.5 text-sm text-neutral-900 focus:outline-none focus:border-black focus:bg-white transition" />
      <div className="flex flex-wrap items-center gap-3">
        <button disabled={busy} onClick={() => run({mode: "deterministic", request_text: request})}
          className="rounded-full bg-[#111418] hover:bg-black px-5 py-2.5 text-xs font-semibold text-white transition disabled:opacity-50 shadow-sm">Interpret entered request</button>
        <span className="text-xs text-neutral-500 font-medium">Live deterministic compilation · no physical verdict until FEA</span>
      </div>
      {!!clarificationExamples.length && <div className="border-t border-neutral-200 pt-4">
        <p className="text-xs uppercase tracking-wider text-neutral-500 font-mono mb-2.5 font-semibold">Recorded Muse clarification questions</p>
        <div className="flex flex-wrap gap-2">{clarificationExamples.map((example) => <button key={example.id} disabled={busy}
          onClick={() => run({mode: "recorded_clarification", example_id: example.id})}
          className="rounded-full border border-neutral-200 bg-neutral-100 px-3.5 py-1.5 text-xs text-neutral-700 hover:bg-neutral-200 transition font-medium disabled:opacity-50">
          {example.id === "Q02" ? "Missing force" : example.id === "Q03" ? "Missing stroke" : example.id === "Q04" ? "Missing material" : example.id === "Q12" ? "Uncertain modulus" : "Material choice"}
        </button>)}</div>
      </div>}
      {!!loopExamples.length && <div className="border-t border-neutral-200 pt-4">
        <p className="text-xs uppercase tracking-wider text-neutral-500 font-mono mb-2.5 font-semibold">Recorded end-to-end solver loops · scripted answers</p>
        <div className="flex flex-wrap gap-2">{loopExamples.map((example) => <button key={example.id} disabled={busy}
          onClick={() => run({mode: "recorded_loop", example_id: example.id})}
          className="rounded-full border border-neutral-200 bg-neutral-100 px-3.5 py-1.5 text-xs text-neutral-700 hover:bg-neutral-200 transition font-medium disabled:opacity-50">
          {example.id === "Q02" ? "Ask force → repair" : example.id === "Q03" ? "Ask stroke → verify" : "Ask material → repair"}
        </button>)}</div>
      </div>}
      {!!localLiveExamples.length && <div className="border-t border-neutral-200 pt-4">
        <p className="text-xs uppercase tracking-wider text-neutral-500 font-mono mb-2.5 font-semibold">Genuine local Muse call + solver · audited replay</p>
        <button disabled={busy} onClick={() => run({mode: "recorded_local_live", example_id: "L01"})}
          className="rounded-full border border-neutral-200 bg-neutral-100 px-3.5 py-1.5 text-xs text-neutral-700 hover:bg-neutral-200 transition font-medium disabled:opacity-50">
          Live Muse question → failed tolerance → robust repair
        </button>
      </div>}
      <div className="border-t border-neutral-200 pt-4">
        <p className="text-xs uppercase tracking-wider text-neutral-500 font-mono mb-2.5 font-semibold">Recorded Muse + physics examples</p>
        <div className="flex flex-wrap gap-2">
          {examples.map((example) => <button key={example.id} disabled={busy}
            onClick={() => run({mode: "recorded_muse", example_id: example.id})}
            className="rounded-full border border-neutral-200 bg-neutral-100 px-3.5 py-1.5 text-xs text-neutral-700 hover:bg-neutral-200 transition font-medium disabled:opacity-50">
            {example.id === "C01" ? "Drift failure" : example.id === "C02" ? "Feasible screen" : example.id === "C09" ? "Contradictory request" : "Safety gate catches model"}
          </button>)}
        </div>
      </div>
      {busy && <p className="text-xs text-neutral-600 font-mono animate-pulse">Reading evidence…</p>}
      {error && <p role="alert" className="text-xs text-rose-600 font-semibold">{error}</p>}
    </div>

    {result && <div className="space-y-4">
      {result.loop && <div className="rounded-2xl border border-neutral-200 bg-white p-6 text-sm shadow-sm">
        <div className="text-xs uppercase tracking-wider text-neutral-500 font-mono font-semibold">Recorded engineering interaction · scripted user answer</div>
        <h3 className="font-bold text-neutral-900 mt-1.5 text-base">Describe → Clarify → Formalize → Simulate → Repair → Verify</h3>
        <p className="mt-3 text-neutral-700"><strong>Muse asked:</strong> {result.loop.muse_question}</p>
        <p className="mt-2 text-neutral-700"><strong>Scripted answer:</strong> {result.loop.scripted_answer}</p>
        <p className="mt-2 text-neutral-700"><strong>Solver:</strong> Five predeclared thicknesses, coarse screening and fine verification of coarse passes. Selected {result.loop.selected_thickness_mm?.toFixed(1) ?? "none"} mm; {result.loop.verdict.replaceAll("_", " ")}.</p>
        <div className="flex flex-wrap gap-2 mt-3">{result.loop.trials.map((trial) => <div key={trial.thickness_mm} className="rounded-xl border border-neutral-200 bg-neutral-50 p-2.5 text-xs font-mono text-neutral-800">
          {trial.thickness_mm.toFixed(1)} mm · {trial.fine_feasible === true ? "fine PASS" : trial.coarse_feasible ? "fine FAIL" : `coarse FAIL ${trial.coarse_failed_gates.join(", ")}`}
        </div>)}</div>
        <p className="text-xs text-neutral-500 mt-3">Solver assumptions: {result.loop.solver_assumptions.join("; ")}. These are recorded scripted fixtures, not live user conversations.</p>
      </div>}
      {result.initial_joint_failure && <div className="rounded-2xl border border-rose-200 bg-rose-50/70 p-5 text-sm text-neutral-800">
        <strong className="text-rose-900">First nominal design failed joint uncertainty.</strong> The {result.initial_joint_failure.candidate_thickness_mm.toFixed(1)} mm candidate drifted {result.initial_joint_failure.absolute_drift_mm.toFixed(4)} mm in the {result.initial_joint_failure.scenario.replaceAll("_", " ")} case, above the {result.initial_joint_failure.drift_limit_mm.toFixed(4)} mm limit. The solver then tested the next predeclared thickness.
      </div>}
      <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap justify-between gap-2 mb-4">
          <h3 className="font-bold text-neutral-900 text-base">Engineering interpretation</h3>
          <span className={`rounded-full px-3 py-1 text-xs font-mono font-semibold ${isRecorded ? "bg-neutral-100 text-neutral-700" : "bg-black text-white"}`}>{result.execution_mode}</span>
        </div>
        <p className="text-sm text-neutral-700 mb-4">{result.request_text}</p>
        <p className="text-sm mb-4 text-neutral-700">Decision: <strong className="text-neutral-900">{result.interpretation.decision.replaceAll("_", " ")}</strong></p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(result.interpretation.constraints).map(([key, value]) => <div key={key} className="rounded-xl border border-neutral-200 bg-neutral-50 p-3.5">
            <div className="text-xs text-neutral-500 font-medium">{LABELS[key] || key}</div>
            <div className="font-mono text-sm mt-1 text-neutral-900 font-bold">{value === null ? <span className="text-amber-700 font-medium">Missing</span> : `${Array.isArray(value) ? value.join(" × ") : value} ${UNITS[key] || ""}`}</div>
          </div>)}
        </div>
        {!!result.interpretation.missing?.length && <p className="text-xs text-amber-800 mt-3 font-medium">Clarify: {result.interpretation.missing.join(", ")}</p>}
        {!!result.interpretation.contradictions?.length && <p className="text-xs text-rose-700 mt-3 font-semibold">Contradiction: {result.interpretation.contradictions.join("; ")}</p>}
        {!!result.interpretation.ambiguities?.length && <p className="text-xs text-amber-800 mt-3 font-medium">Ambiguity: {result.interpretation.ambiguities.join("; ")}</p>}
        {!!result.interpretation.uncertainties?.length && <p className="text-xs text-amber-800 mt-3 font-medium">Material uncertainty: {result.interpretation.uncertainties.join("; ")}</p>}
        {!!result.interpretation.model_issue_codes?.length && <p className="text-xs text-neutral-700 mt-3">Model claimed issue codes: {result.interpretation.model_issue_codes.join(", ")}</p>}
        {result.execution_mode === "RECORDED_MUSE_CLARIFICATION" && result.reference_score && <p className={`text-xs mt-3 ${result.reference_score.full_case ? "text-emerald-700" : "text-amber-800"}`}>Frozen benchmark exact-case score: {result.reference_score.full_case ? "PASS" : "FAIL"}. A failed case may still contain a useful question; inspect the claimed constraints and issue codes.</p>}
        {result.interpretation.material_properties?.measured_E_gpa != null && <p className="text-xs text-neutral-900 font-mono mt-3">Measured batch modulus: {result.interpretation.material_properties.measured_E_gpa} GPa</p>}
        {result.clarification?.action === "clarify" && <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/70 p-4">
          <p className="text-sm text-amber-900 font-medium">Next question: {result.clarification.question}</p>
          <div className="flex flex-wrap gap-2 mt-3">
            <input aria-label="Answer clarification question" value={answer} onChange={(event) => setAnswer(event.target.value)}
              className="min-w-44 flex-1 rounded-xl border border-neutral-300 bg-white p-2.5 text-sm text-neutral-900 focus:outline-none focus:border-black" placeholder="Enter the missing value" />
            <button disabled={busy || !answer.trim()} onClick={() => {
              const prefix: Record<string, string> = {force_n: "force", stroke_min_mm: "stroke", material: "material", envelope_mm: "package", material_properties: "measured modulus"};
              const field = result.clarification?.field || "";
              const next = `${result.request_text} ${prefix[field] || field} ${answer.trim()}.`;
              setAnswer("");
              run({mode: "deterministic", request_text: next});
            }} className="rounded-full bg-[#111418] hover:bg-black px-4 py-2 text-xs font-semibold text-white transition disabled:opacity-50">Apply answer</button>
          </div>
          <p className="text-xs text-neutral-500 mt-2">Answer compilation is deterministic; no new Muse or FEA call. {result.clarification.remaining_required?.length ?? (result.clarification.field ? 1 : 0)} field(s) requested.</p>
        </div>}
        {result.clarification?.action === "abstain" && <p className="text-xs text-rose-700 mt-3 font-semibold">Clarification halted: {result.clarification.reason}</p>}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm">
          <h3 className="font-bold text-neutral-900 mb-3 text-base">Scientific plan</h3>
          <ol className="list-decimal pl-5 space-y-2 text-sm text-neutral-700">{result.scientific_plan.map((step, i) => <li key={i}>{step}</li>)}</ol>
          {result.safety_gate?.startsWith("blocked") && <p className="text-xs text-rose-700 font-semibold mt-4">Independent safety gate blocked this model output.</p>}
        </div>
        <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm">
          <h3 className="font-bold text-neutral-900 mb-3 text-base">Physics verification</h3>
          {result.physics ? <>
            <p className={`text-sm font-bold ${result.physics.feasible ? "text-emerald-700" : "text-rose-700"}`}>{result.physics.feasible ? "Beam-model screen passed" : `Rejected: ${failedGates.join(", ") || "solver failure"}`}</p>
            <div className="mt-3"><GraphSketch graph={result.physics.graph} envelope={result.physics.envelope_mm} /></div>
            <div className="grid grid-cols-3 gap-2 mt-4 font-mono text-xs text-neutral-800">
              <div className="bg-neutral-50 p-2 rounded-lg border border-neutral-200">Stroke<br/><strong className="text-neutral-900">{result.physics.stroke_mm.toFixed(3)} mm</strong></div>
              <div className="bg-neutral-50 p-2 rounded-lg border border-neutral-200">Abs. drift<br/><strong className="text-neutral-900">{result.physics.absolute_drift_mm.toFixed(3)} mm</strong></div>
              <div className="bg-neutral-50 p-2 rounded-lg border border-neutral-200">Stress<br/><strong className="text-neutral-900">{result.physics.stress_mpa.toFixed(2)} MPa</strong></div>
            </div>
            <div className="mt-4 text-xs text-neutral-500 space-y-1">
              {Object.entries(result.physics.constraint_margins).map(([key, margin]) => <p key={key}>{key.replaceAll("_", " ")} margin: <span className={margin >= 0 ? "text-emerald-700 font-bold" : "text-rose-700 font-bold"}>{margin.toFixed(3)}</span></p>)}
              <p>Mesh: {result.physics.mesh_elements_per_beam} elements per beam · candidate: deterministic two-stage template</p>
            </div>
          </> : <p className="text-sm text-neutral-500">No physical result for this interpretation. A valid specification and solver run are required.</p>}
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

    <p className="text-xs text-neutral-500">Frozen 16-request specification result: Muse cold 15/16, rules 7/16. The 20-request clarification memory arms each scored 16/20; each Muse arm made one unsupported field assumption. On the fresh 12-request transfer set Muse made no unsupported field assumptions. The hosted Muse and FEA results are recorded replays; all clarification answers shown here are scripted. See the public evidence for task-level results and limitations.</p>
  </div>;
}

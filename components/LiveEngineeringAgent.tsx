"use client";

import { useEffect, useState } from "react";
import LiveGraph3D, { type LiveGraph } from "./LiveGraph3D";

type Job = {
  id: string; status: string; execution_mode: string; error?: string;
  job_token?: string;
  request_text?: string; repair_mode?: string;
  interpretation?: { decision: string; constraints: Record<string, string | number | number[] | null> } | null;
  specification?: { constraints: Record<string, string | number | number[] | null> } | null;
  question?: { text: string; source: string } | null;
  selected_mm?: number | null; selected_design?: string | null; selection_source?: string | null;
  selected_proposal?: Graph | null; geometry_family?: string; verdict?: string;
  repair_attempt?: {
    verdict: string; failed_scenario: string;
    measured_failure?: { failed_gates: string[]; stroke_margin_mm?: number; drift_margin_mm?: number; stress_margin_mpa?: number; thickness_margin_mm?: number; reason?: string };
    hypothesis?: { diagnosis: string; failed_gate: string; action: string; predicted_stroke_direction: string; predicted_drift_direction: string };
    prediction_check?: { both_correct: boolean | null; predicted: Record<string, string>; measured: Record<string, string> };
    measured_failed_scenario_after?: { stroke_mm: number; absolute_drift_mm: number; feasible: boolean };
  } | null;
  provenance?: { model: string; request_id: string; estimated_cost_usd: number }[];
  events: { at_utc: string; step: string; detail: unknown }[];
  trials?: { thickness_mm: number; coarse: { feasible: boolean; stroke_mm?: number; absolute_drift_mm?: number; gates?: Record<string, boolean> }; fine?: { feasible: boolean } | null; joint_corners?: { name: string; result: { feasible: boolean } }[] }[];
};

type Graph = LiveGraph;

function GraphPlan({ graph }: { graph: Graph }) {
  const points = graph.anchors.concat(graph.stages.map(s => s.center));
  const width = Math.max(...points.map(p => p[0])) * 1000;
  const height = Math.max(...points.map(p => p[1])) * 1000 + 12;
  const point = (kind: string, index: number, port: string) => {
    if (kind === "anchor") return graph.anchors[index];
    const stage = graph.stages[index];
    return [stage.center[0], stage.center[1] + (port === "top" ? stage.height / 2 : port === "bot" ? -stage.height / 2 : 0)];
  };
  return <svg role="img" aria-label="Plan view of the actual selected beam geometry" viewBox={`-3 -3 ${width + 6} ${height + 6}`} className="h-48 w-full rounded border border-cyan-900 bg-black">
    {graph.connections.map((e, i) => { const a = point(e.from_type, e.from_index, e.from_port); const b = point(e.to_type, e.to_index, e.to_port); return <line key={i} x1={a[0] * 1000} y1={height - a[1] * 1000} x2={b[0] * 1000} y2={height - b[1] * 1000} stroke="#22d3ee" strokeWidth={Math.max(.6, e.thickness * 1400)} />; })}
    {graph.stages.map((s, i) => <line key={i} x1={s.center[0] * 1000} y1={height - (s.center[1] - s.height / 2) * 1000} x2={s.center[0] * 1000} y2={height - (s.center[1] + s.height / 2) * 1000} stroke="#a5b4fc" strokeWidth="2" />)}
    {graph.anchors.map((a, i) => <circle key={i} cx={a[0] * 1000} cy={height - a[1] * 1000} r="1.5" fill="#fbbf24" />)}
  </svg>;
}

const EXAMPLE = "Design a PP guide for a 6 N load, 1.2 mm stroke, 75 x 50 mm package, drift under 0.03 mm, and stress under 20 MPa.";

export default function LiveEngineeringAgent() {
  const [capable, setCapable] = useState(false);
  const [checkingCapability, setCheckingCapability] = useState(true);
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  const [accessCode, setAccessCode] = useState("");
  const [requestText, setRequestText] = useState(EXAMPLE);
  const [repairMode, setRepairMode] = useState<"deterministic" | "muse_directed" | "muse_validated_memory" | "muse_casm_repair">("muse_directed");
  const [answer, setAnswer] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [recordedEpisode, setRecordedEpisode] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    let retryTimer: number | undefined;
    const probe = async (attempt: number) => {
      try {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 15000);
        let response: Response;
        try { response = await fetch("/backend/api/live/capabilities", { signal: controller.signal, cache: "no-store" }); }
        finally { window.clearTimeout(timeout); }
        if (!response.ok) throw new Error(`Capability check returned ${response.status}`);
        const data = await response.json();
        if (active) { setCapable(Boolean(data.enabled)); setCheckingCapability(false); }
      } catch {
        if (!active) return;
        if (attempt < 11) retryTimer = window.setTimeout(() => probe(attempt + 1), 5000);
        else { setCapable(false); setCheckingCapability(false); }
      }
    };
    void probe(0);
    return () => { active = false; if (retryTimer) window.clearTimeout(retryTimer); };
  }, [connectionAttempt]);
  useEffect(() => {
    if (!job || !["model_running", "screening"].includes(job.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`/backend/api/live/${job.id}/status`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ access_code: accessCode, job_token: job.job_token }) });
        if (response.ok) { const data = await response.json(); setJob(previous => ({ ...data, job_token: previous?.job_token })); }
      } catch { /* The next poll can recover a transient network failure. */ }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [job?.id, job?.status, accessCode]);

  async function send(path: string, payload: Record<string, string>) {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/backend/api/live/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, access_code: accessCode, ...(path === "start" ? {} : { job_token: job?.job_token }) }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
      setJob({ ...data, job_token: data.job_token || job?.job_token });
      if (path === "start") setRecordedEpisode(false);
      setAnswer("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Request failed"); }
    finally { setBusy(false); }
  }

  async function inspectHostedEpisode() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/evidence/r91_hosted_c01.json");
      if (!response.ok) throw new Error(`Saved hosted episode unavailable (${response.status})`);
      const evidence = await response.json();
      setJob({ ...evidence.job, execution_mode: "RECORDED_HOSTED_R9_CASM_REPAIR" });
      setRecordedEpisode(true);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Saved episode unavailable"); }
    finally { setBusy(false); }
  }

  return <section className="rounded-xl border border-cyan-800/60 bg-neutral-950 p-5 space-y-4" aria-label="Live engineering agent">
    <div><h2 className="text-lg font-semibold text-cyan-300">Live Muse + beam screening</h2>
      <p className="text-sm text-neutral-400">A fresh Meta Muse interpretation and nonlinear beam solve for your typed request. Restricted to a scaled PP/PETG two-stage family within 55–110 × 35–75 mm. Numerical screening only; fabrication and clearance are unverified.</p>
      <p className="mt-2 text-xs text-emerald-300">Production run verified: one fresh Muse receipt, five FEA trials; 0.9 mm failed 1/4 uncertainty corners, 1.0 mm passed 4/4. <a className="underline" href="https://github.com/AmanM006/meta-generative-cad/blob/master/research-source/fresh_evidence/live_c01_hosted_2026_11_04.json" target="_blank" rel="noreferrer">Inspect hosted result</a></p>
      <p className="mt-1 text-xs text-neutral-400">Exploratory five-case repair audit: deterministic rule 4/5, Muse repair 4/5, Muse with retrieved CASM context 5/5 before fallback; deterministic sweep 5/5. <a className="underline" href="https://github.com/AmanM006/meta-generative-cad/blob/master/research-source/RELEASE_R9_VERIFICATION.md" target="_blank" rel="noreferrer">Methods and limits</a></p>
      <button onClick={inspectHostedEpisode} disabled={busy} className="mt-2 rounded border border-violet-700 px-3 py-1 text-xs text-violet-200 disabled:opacity-40">Inspect verified hosted R9 episode</button><span className="ml-2 text-xs text-neutral-500">Saved production run with two Meta receipts and fresh beam FEA; clicking replays evidence without a new call.</span></div>
    <div className="grid gap-3 md:grid-cols-[1fr_12rem]">
      <div className="space-y-2"><textarea aria-label="Engineering request" value={requestText} onChange={e => setRequestText(e.target.value)} rows={3} className="w-full rounded border border-neutral-700 bg-black p-3 text-sm" />
        <div className="flex flex-wrap gap-2 text-xs"><button onClick={() => setRequestText(EXAMPLE)} className="rounded border border-neutral-700 px-2 py-1">C01 verification</button><button onClick={() => setRequestText("Design a PP guide under 4 N load requiring 0.7 mm stroke in a 60 x 40 mm package, with drift under 0.035 mm and stress under 25 MPa.")} className="rounded border border-neutral-700 px-2 py-1">Compact package</button><button onClick={() => setRequestText("Build a PETG compliant guide for 6 N load, 1.0 mm stroke, 85 x 55 mm package, drift under 0.035 mm, and stress under 30 MPa.")} className="rounded border border-neutral-700 px-2 py-1">PETG material</button></div>
        <label className="block text-xs text-neutral-400">Correction policy
          <select value={repairMode} onChange={e => setRepairMode(e.target.value as typeof repairMode)} className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white">
            <option value="muse_directed">Muse chooses one corrective experiment</option>
            <option value="deterministic">Deterministic thickness search</option>
            <option value="muse_validated_memory">Muse with validated failure memory</option>
            <option value="muse_casm_repair">Muse with retrieved CASM context</option>
          </select>
        </label>
        <p className="text-xs text-neutral-500">Every proposed change is checked by fresh FEA. If a Muse repair fails, the deterministic fallback is labeled.</p></div>
      <div className="space-y-2"><label className="block text-xs text-neutral-400">Demo access code<input type="password" autoComplete="off" value={accessCode} onChange={e => setAccessCode(e.target.value)} className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white" /></label>
        <button disabled={!capable || busy || accessCode.length < 8} onClick={() => send("start", { request_text: requestText, repair_mode: repairMode })} className="w-full rounded bg-cyan-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-40">Run fresh analysis</button>
        <p className="text-xs text-neutral-500">{checkingCapability ? "Connecting to live service; free-tier wake-up may take a minute." : capable ? "Live service available. Access code required." : "Live service unavailable. Replay examples remain available below."}</p>
        {!capable && !checkingCapability && <button className="text-xs text-cyan-300 underline" onClick={() => { setCheckingCapability(true); setConnectionAttempt(n => n + 1); }}>Retry live connection</button>}</div>
    </div>
    {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
    {job && <div className="space-y-3 text-sm">
      {recordedEpisode && <p className="rounded border border-violet-700 bg-violet-950/40 p-2 text-xs text-violet-100">Recorded hosted evidence · this view does not make a new Meta call. The original job completed on Render and its redacted result is public.</p>}
      <p className="font-mono text-cyan-200">{job.execution_mode} · {job.status} · {job.id.slice(0, 8)}</p>
      <div className="grid gap-3 md:grid-cols-2"><div className="rounded border border-neutral-800 p-3"><h3 className="font-semibold text-neutral-300">1 · Describe and interpret</h3><p className="mt-1 text-neutral-400">{job.request_text}</p><p className="mt-2 text-xs text-cyan-300">Muse decision: {job.interpretation?.decision || "pending"}</p></div>
        <div className="rounded border border-neutral-800 p-3"><h3 className="font-semibold text-neutral-300">2 · Formal constraints</h3><dl className="mt-1 grid grid-cols-2 gap-1 text-xs">{Object.entries(job.specification?.constraints || {}).map(([key, value]) => <div key={key}><dt className="text-neutral-500">{key}</dt><dd>{Array.isArray(value) ? value.join(" × ") : value ?? "unknown"}</dd></div>)}</dl></div></div>
      {job.error && <p role="alert" className="text-red-300">{job.error}</p>}
      {job.question && <div className="rounded border border-amber-700/50 p-3"><p>{job.question.text} <span className="text-xs text-neutral-500">({job.question.source})</span></p>
        <div className="mt-2 flex gap-2"><input aria-label="Clarification answer" value={answer} onChange={e => setAnswer(e.target.value)} className="min-w-0 flex-1 rounded border border-neutral-700 bg-black p-2" /><button disabled={busy || !answer.trim()} onClick={() => send(`${job.id}/answer`, { answer })} className="rounded bg-amber-700 px-3 disabled:opacity-40">Answer</button></div></div>}
      {job.repair_attempt && <div className="rounded border border-violet-800/70 bg-violet-950/20 p-3 space-y-2"><h3 className="font-semibold text-violet-200">3 · Diagnose and revise from measured failure</h3>
        {job.repair_attempt.measured_failure && <p>Failed {job.repair_attempt.failed_scenario} corner: {job.repair_attempt.measured_failure.failed_gates.join(", ")}. {job.repair_attempt.measured_failure.drift_margin_mm != null ? `Drift margin ${job.repair_attempt.measured_failure.drift_margin_mm.toFixed(4)} mm; stroke margin ${job.repair_attempt.measured_failure.stroke_margin_mm?.toFixed(4)} mm.` : `Minimum thickness margin ${job.repair_attempt.measured_failure.thickness_margin_mm?.toFixed(4)} mm. ${job.repair_attempt.measured_failure.reason || ""}`}</p>}
        {job.repair_attempt.hypothesis && <><p><strong>Muse hypothesis:</strong> {job.repair_attempt.hypothesis.diagnosis}</p><p><strong>Chosen experiment:</strong> {job.repair_attempt.hypothesis.action}</p></>}
        {job.repair_attempt.prediction_check && <p>Predicted stroke/drift: {job.repair_attempt.prediction_check.predicted.stroke}/{job.repair_attempt.prediction_check.predicted.drift}. Measured: {job.repair_attempt.prediction_check.measured.stroke}/{job.repair_attempt.prediction_check.measured.drift}. {job.repair_attempt.prediction_check.both_correct == null ? "Directions unscorable because baseline corner had no FEA response." : job.repair_attempt.prediction_check.both_correct ? "Both directions matched." : "At least one prediction was falsified."}</p>}
        <p className="text-xs text-neutral-400">FEA verdict: {job.repair_attempt.verdict}</p></div>}
      {job.verdict && <p className={job.status === "completed" ? "text-emerald-300" : "text-amber-300"}>4 · {job.verdict} · {job.selected_design || "No robust candidate"}<span className="block text-xs text-neutral-400">Selection: {job.selection_source || "none"}. Numerical 2D beam screen; clearance and fabrication unverified.</span></p>}
      {job.selected_proposal && <div><h3 className="mb-2 text-sm font-semibold text-neutral-300">Selected evaluated geometry</h3><div className="grid gap-3 lg:grid-cols-2"><LiveGraph3D graph={job.selected_proposal} /><GraphPlan graph={job.selected_proposal} /></div><p className="mt-1 text-xs text-neutral-500">{job.geometry_family}. Both geometry views show the selected graph; the solver is a 2D beam model. Clearance and fabrication remain unverified.</p></div>}
      {!!job.trials?.length && <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="text-neutral-400"><th>Thickness</th><th>Coarse</th><th>Fine</th><th>Joint corners</th><th>Stroke</th><th>Drift</th></tr></thead><tbody>{job.trials.map(t => <tr key={t.thickness_mm} className="border-t border-neutral-800"><td>{t.thickness_mm.toFixed(1)} mm</td><td>{t.coarse.feasible ? "pass" : "fail"}</td><td>{t.fine ? t.fine.feasible ? "pass" : "fail" : "—"}</td><td>{t.joint_corners?.filter(c => c.result.feasible).length || 0}/{t.joint_corners?.length || 0}</td><td>{t.coarse.stroke_mm?.toFixed(3) ?? "—"} mm</td><td>{t.coarse.absolute_drift_mm?.toFixed(4) ?? "—"} mm</td></tr>)}</tbody></table></div>}
      <p className="text-xs text-neutral-500">Model receipts: {job.provenance?.map(p => `${p.model} ${p.request_id}`).join(", ") || "pending"}. API prices are estimates; actual billing is unknown.</p>
      <details><summary className="cursor-pointer text-xs text-neutral-400">Execution trace ({job.events.length} events)</summary><ol className="mt-2 max-h-64 space-y-1 overflow-y-auto font-mono text-xs text-neutral-400">{job.events.map((e, i) => <li key={i}>{e.at_utc} · {e.step} · {JSON.stringify(e.detail)}</li>)}</ol></details>
    </div>}
  </section>;
}

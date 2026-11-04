"use client";

import { useEffect, useState } from "react";

type Job = {
  id: string; status: string; execution_mode: string; error?: string;
  question?: { text: string; source: string } | null;
  selected_mm?: number | null; verdict?: string;
  provenance?: { model: string; request_id: string; estimated_cost_usd: number }[];
  events: { at_utc: string; step: string; detail: unknown }[];
  trials?: { thickness_mm: number; coarse: { feasible: boolean; stroke_mm?: number; absolute_drift_mm?: number; gates?: Record<string, boolean> }; fine?: { feasible: boolean } | null; joint_corners?: { name: string; result: { feasible: boolean } }[] }[];
};

const EXAMPLE = "Design a PP guide for a 6 N load, 1.2 mm stroke, 75 x 50 mm package, drift under 0.03 mm, and stress under 20 MPa.";

export default function LiveEngineeringAgent() {
  const [capable, setCapable] = useState(false);
  const [accessCode, setAccessCode] = useState("");
  const [requestText, setRequestText] = useState(EXAMPLE);
  const [answer, setAnswer] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch("/backend/api/live/capabilities").then(r => r.json()).then(d => setCapable(Boolean(d.enabled))).catch(() => setCapable(false));
  }, []);
  useEffect(() => {
    if (!job || !["model_running", "screening"].includes(job.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`/backend/api/live/${job.id}/status`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ access_code: accessCode }) });
        if (response.ok) setJob(await response.json());
      } catch { /* The next poll can recover a transient network failure. */ }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [job?.id, job?.status, accessCode]);

  async function send(path: string, payload: Record<string, string>) {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/backend/api/live/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, access_code: accessCode }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
      setJob(data);
      setAnswer("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Request failed"); }
    finally { setBusy(false); }
  }

  return <section className="rounded-xl border border-cyan-800/60 bg-neutral-950 p-5 space-y-4" aria-label="Live engineering agent">
    <div><h2 className="text-lg font-semibold text-cyan-300">Live Muse + beam screening</h2>
      <p className="text-sm text-neutral-400">A fresh Meta Muse interpretation and nonlinear beam solve for your typed request. Restricted to a 75 × 50 mm PP/PETG two-stage family. Numerical screening only; fabrication and clearance are unverified.</p></div>
    <div className="grid gap-3 md:grid-cols-[1fr_12rem]">
      <textarea aria-label="Engineering request" value={requestText} onChange={e => setRequestText(e.target.value)} rows={3} className="rounded border border-neutral-700 bg-black p-3 text-sm" />
      <div className="space-y-2"><label className="block text-xs text-neutral-400">Demo access code<input type="password" autoComplete="off" value={accessCode} onChange={e => setAccessCode(e.target.value)} className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white" /></label>
        <button disabled={!capable || busy || accessCode.length < 8} onClick={() => send("start", { request_text: requestText })} className="w-full rounded bg-cyan-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-40">Run fresh analysis</button>
        <p className="text-xs text-neutral-500">{capable ? "Live service available. Access code required." : "Live service is not configured. Replay examples remain available below."}</p></div>
    </div>
    {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
    {job && <div className="space-y-3 text-sm">
      <p className="font-mono text-cyan-200">{job.execution_mode} · {job.status} · {job.id.slice(0, 8)}</p>
      {job.error && <p role="alert" className="text-red-300">{job.error}</p>}
      {job.question && <div className="rounded border border-amber-700/50 p-3"><p>{job.question.text} <span className="text-xs text-neutral-500">({job.question.source})</span></p>
        <div className="mt-2 flex gap-2"><input aria-label="Clarification answer" value={answer} onChange={e => setAnswer(e.target.value)} className="min-w-0 flex-1 rounded border border-neutral-700 bg-black p-2" /><button disabled={busy || !answer.trim()} onClick={() => send(`${job.id}/answer`, { answer })} className="rounded bg-amber-700 px-3 disabled:opacity-40">Answer</button></div></div>}
      {job.verdict && <p className={job.selected_mm == null ? "text-amber-300" : "text-emerald-300"}>{job.verdict}{job.selected_mm != null ? ` · ${job.selected_mm.toFixed(1)} mm flexures` : ""}</p>}
      {!!job.trials?.length && <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="text-neutral-400"><th>Thickness</th><th>Coarse</th><th>Fine</th><th>Joint corners</th><th>Stroke</th><th>Drift</th></tr></thead><tbody>{job.trials.map(t => <tr key={t.thickness_mm} className="border-t border-neutral-800"><td>{t.thickness_mm.toFixed(1)} mm</td><td>{t.coarse.feasible ? "pass" : "fail"}</td><td>{t.fine ? t.fine.feasible ? "pass" : "fail" : "—"}</td><td>{t.joint_corners?.filter(c => c.result.feasible).length || 0}/{t.joint_corners?.length || 0}</td><td>{t.coarse.stroke_mm?.toFixed(3) ?? "—"} mm</td><td>{t.coarse.absolute_drift_mm?.toFixed(4) ?? "—"} mm</td></tr>)}</tbody></table></div>}
      <p className="text-xs text-neutral-500">Model receipts: {job.provenance?.map(p => `${p.model} ${p.request_id}`).join(", ") || "pending"}. API prices are estimates; actual billing is unknown.</p>
      <details><summary className="cursor-pointer text-xs text-neutral-400">Execution trace ({job.events.length} events)</summary><ol className="mt-2 max-h-64 space-y-1 overflow-y-auto font-mono text-xs text-neutral-400">{job.events.map((e, i) => <li key={i}>{e.at_utc} · {e.step} · {JSON.stringify(e.detail)}</li>)}</ol></details>
    </div>}
  </section>;
}

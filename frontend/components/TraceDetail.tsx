"use client";

import { useEffect, useState } from "react";

type TraceData = { trace: Record<string, unknown>; spans: Record<string, unknown>[]; logs: Record<string, unknown>[] };

export default function TraceDetail({ traceId }: { traceId: string }) {
  const [data, setData] = useState<TraceData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch(`/api/traces/${encodeURIComponent(traceId)}`)
      .then((response) => { if (!response.ok) throw new Error(`Trace lookup failed (${response.status})`); return response.json(); })
      .then(setData)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Trace unavailable"));
  }, [traceId]);
  if (error) return <div className="table-empty error-note">{error}</div>;
  if (!data) return <div className="table-empty">Loading trace…</div>;
  return <div className="trace-detail"><div className="trace-summary"><span>Status <strong>{String(data.trace.status)}</strong></span><span>Duration <strong>{String(data.trace.duration_ms)} ms</strong></span><span>Request <strong>{String(data.trace.request_id)}</strong></span></div>
    <div className="trace-waterfall">{data.spans.map((span) => <div className="trace-span" key={String(span.span_id)}><span className="trace-mark" /><div className="trace-span-info"><strong>{String(span.name).replaceAll("_", " ")}</strong><small>{String(span.span_type)} · {String(span.status)}</small></div><div className="trace-bar-track"><div className="trace-bar" style={{ width: `${Math.max(8, Math.min(100, Number(span.duration_ms) / Math.max(1, Number(data.trace.duration_ms)) * 100))}%` }} /></div><span className="trace-duration">{Number(span.duration_ms).toFixed(1)} ms</span><details className="trace-metadata"><summary>Details</summary><pre>{JSON.stringify(JSON.parse(String(span.metadata)), null, 2)}</pre></details></div>)}</div>
    <h2 className="trace-section-title">Correlated logs</h2><pre className="trace-json">{JSON.stringify(data.logs.map((log) => ({ timestamp: log.timestamp, service: log.service, message: log.message, status: log.status })), null, 2)}</pre>
  </div>;
}
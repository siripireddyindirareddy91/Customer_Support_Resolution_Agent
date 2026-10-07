"use client";

import { useEffect, useState } from "react";

type Overview = {
  requests: { total: number; successful: number; failed: number; success_rate: number | null; average_latency_ms: number | null; max_latency_ms: number | null };
  traces: number;
  logs: number;
  agent_runs: { total: number; failed: number };
  source: string;
};

export default function MetricsSummary() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch("/api/observability/overview")
      .then((response) => { if (!response.ok) throw new Error("Telemetry API unavailable"); return response.json(); })
      .then(setData)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Telemetry unavailable"));
  }, []);

  const values = [
    ["Requests", data?.requests.total ?? "—", `${data?.requests.successful ?? 0} successful`],
    ["Success rate", data?.requests.success_rate == null ? "—" : `${(data.requests.success_rate * 100).toFixed(1)}%`, `${data?.requests.failed ?? 0} failed`],
    ["Average latency", data?.requests.average_latency_ms == null ? "—" : `${data.requests.average_latency_ms} ms`, "Measured API duration"],
    ["Traces", data?.traces ?? "—", `${data?.agent_runs.total ?? 0} workflow runs`],
  ];

  return <>
    {error && <div className="error-note">{error}</div>}
    <section className="metrics" aria-label="Observed request metrics">{values.map(([label, value, note]) => <div className="metric" key={String(label)}><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-note">{note}</div></div>)}</section>
    <div className="telemetry-source">{data ? `Measured from ${data.source} · ${data.logs} structured events stored` : "Waiting for telemetry data…"}</div>
  </>;
}